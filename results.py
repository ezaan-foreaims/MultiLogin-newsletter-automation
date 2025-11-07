import json, time

def save_results(results, filename="results.json"):
    ts = time.strftime("%Y%m%d_%H%M%S")
    data = {"timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total": len(results),
            "successful": sum(1 for _,s in results if s),
            "failed": sum(1 for _,s in results if not s),
            "results":[{"url":u,"success":s} for u,s in results]}
    output_file = f"results_{ts}.json"
    with open(output_file,'w',encoding='utf-8') as f: json.dump(data,f,indent=2)
    return output_file
