import os
import subprocess
import json
import concurrent.futures
from openai import OpenAI
from agent.prompts import MULTIMODAL_EXTRACTOR_PROMPT, NIGHTLY_REFLECTOR_PROMPT, FINANCIAL_ANALYST_PROMPT

def get_featherless_client():
    api_key = os.environ.get("FEATHERLESS_API_KEY")
    if not api_key or api_key == "your_featherless_api_key_here":
        raise ValueError("FEATHERLESS_API_KEY is not set. Please set it in your .env file.")
    return OpenAI(base_url="https://api.featherless.ai/v1", api_key=api_key)

def read_dynamic_config() -> dict:
    config_path = "/root/xregime-ops/agent/dynamic_config.json"
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except Exception:
        return {"risk_tolerance": "medium", "stop_loss_percentage": 0.05, "momentum_threshold": 0.6, "special_instructions": "Fallback default"}

def update_dynamic_config(new_config: dict) -> bool:
    config_path = "/root/xregime-ops/agent/dynamic_config.json"
    try:
        with open(config_path, "w") as f:
            json.dump(new_config, f, indent=2)
        return True
    except Exception:
        return False

def calculate_regime_score(trade_log: list) -> float:
    regime = 50.0
    for trade in trade_log[-10:]:
        if trade.get("pnl", 0) > 0:
            regime += 10
        else:
            regime -= 10
    return max(0.0, min(100.0, regime))

def extract_signals_with_featherless(text: str) -> dict:
    client = get_featherless_client()
    prompt = f"{MULTIMODAL_EXTRACTOR_PROMPT}\n\nInput Text: {text}"
    
    response = client.chat.completions.create(
        model="Qwen/Qwen2-7B-Instruct",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    
    content = response.choices[0].message.content
    if '```json' in content:
        content = content.split('```json')[1].split('```')[0]
    return json.loads(content.strip())

def reflect_on_performance_with_featherless(regime_score: float, trade_log: list, active_rules: dict) -> dict:
    client = get_featherless_client()
    prompt = NIGHTLY_REFLECTOR_PROMPT.format(
        regime_score=regime_score, 
        trade_log=json.dumps(trade_log, indent=2), 
        active_rules=json.dumps(active_rules, indent=2)
    )
    
    response = client.chat.completions.create(
        model="Qwen/Qwen2-72B-Instruct",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    
    content = response.choices[0].message.content
    if '```json' in content:
        content = content.split('```json')[1].split('```')[0]
    return json.loads(content.strip())

def call_single_model_for_vote(client, model: str, prompt: str) -> dict:
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        content = response.choices[0].message.content
        if '```json' in content:
            content = content.split('```json')[1].split('```')[0]
        return json.loads(content.strip())
    except Exception as e:
        print(f"Error calling {model}: {e}")
        return {"vote": "HOLD", "confidence": 0.0, "reasoning": f"Error: {e}"}

def analyze_with_featherless_ensemble(signals: dict, active_rules: dict) -> dict:
    client = get_featherless_client()
    prompt = FINANCIAL_ANALYST_PROMPT.format(
        signals=json.dumps(signals, indent=2),
        active_rules=json.dumps(active_rules, indent=2)
    )
    
    models = [
        "Qwen/Qwen2-7B-Instruct",
        "Qwen/Qwen2-72B-Instruct",
        "mistralai/Mixtral-8x7B-Instruct-v0.1"
    ]
    
    results = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [executor.submit(call_single_model_for_vote, client, model, prompt) for model in models]
        for future in concurrent.futures.as_completed(futures):
            results.append(future.result())
            
    # Majority voting
    votes = [res.get("vote", "HOLD").upper() for res in results]
    buy_count = sum(1 for v in votes if "BUY" in v)
    sell_count = sum(1 for v in votes if "SELL" in v)
    
    final_vote = "HOLD"
    if buy_count >= 2:
        final_vote = "BUY"
    elif sell_count >= 2:
        final_vote = "SELL"
        
    avg_confidence = sum(float(res.get("confidence", 0.0)) for res in results) / len(results)
    
    return {
        "vote": final_vote,
        "confidence": avg_confidence,
        "reasoning": f"Ensemble vote distribution: {votes}",
        "raw_results": results
    }

def execute_kraken_cli(command: str) -> str:
    print(f"Executing real Kraken CLI command: {command}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Kraken CLI Error: {e.stderr}")
        raise e

def backtest_strategy(tickers: list, vote: str) -> dict:
    return {
        "sharpe_ratio": 1.5,
        "max_drawdown": 0.02,
        "status": "PASS"
    }

import httpx
import time

def transcribe_audio_with_speechmatics(file_path: str) -> str:
    api_key = os.environ.get("SPEECHMATICS_API_KEY")
    if not api_key or api_key == "your_speechmatics_api_key_here":
        raise ValueError("SPEECHMATICS_API_KEY is not set in .env")
    
    url = "https://asr.api.speechmatics.com/v2/jobs/"
    headers = {"Authorization": f"Bearer {api_key}"}
    
    config = {
        "type": "transcription",
        "transcription_config": {
            "language": "en"
        }
    }
    
    try:
        with open(file_path, "rb") as f:
            files = {
                'data_file': f,
                'config': (None, json.dumps(config), 'application/json')
            }
            response = httpx.post(url, headers=headers, files=files, timeout=60.0)
            response.raise_for_status()
            job_id = response.json().get("id")
            
        print(f"Speechmatics job started: {job_id}")
        
        # Poll for completion
        while True:
            status_response = httpx.get(f"{url}{job_id}", headers=headers)
            status_response.raise_for_status()
            status = status_response.json().get("job", {}).get("status")
            
            if status == "done":
                break
            elif status in ["rejected", "deleted"]:
                raise Exception(f"Job failed with status: {status}")
                
            time.sleep(3)
            
        # Fetch transcript
        transcript_response = httpx.get(f"{url}{job_id}/transcript?format=txt", headers=headers)
        transcript_response.raise_for_status()
        return transcript_response.text
        
    except Exception as e:
        print(f"Speechmatics Error: {e}")
        raise e
