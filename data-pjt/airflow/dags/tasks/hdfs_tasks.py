import requests
from datetime import datetime, timedelta

def cleanup_old_hdfs_partitions():
    # 30일 이전의 데이터를 삭제 타겟으로 설정
    retention_days = 30
    cutoff_date = datetime.now() - timedelta(days=retention_days)
    cutoff_str = cutoff_date.strftime("%Y%m%d")
    
    print(f"Starting HDFS cleanup. Retention policy: {retention_days} days. Cutoff Date: {cutoff_str}")
    
    # HDFS WebHDFS API를 이용해 관리하는 디렉토리들의 목록을 조회합니다.
    hdfs_base_urls = [
        "http://namenode:9870/webhdfs/v1/raw/bonds",
        "http://namenode:9870/webhdfs/v1/dw/bonds",
        "http://namenode:9870/webhdfs/v1/raw/news"
    ]
    
    for base_url in hdfs_base_urls:
        list_url = f"{base_url}?op=LISTSTATUS"
        try:
            resp = requests.get(list_url, timeout=15)
            if resp.status_code == 200:
                statuses = resp.json().get("FileStatuses", {}).get("FileStatus", [])
                for status in statuses:
                    path_suffix = status.get("pathSuffix", "")
                    # 파티션 디렉토리는 'bas_dt=YYYYMMDD' 형식을 가집니다.
                    if path_suffix.startswith("bas_dt="):
                        dt_str = path_suffix.split("=")[1]
                        # 날짜 문자열이 YYYYMMDD 형태이고 cutoff_str보다 작다면 삭제
                        if len(dt_str) == 8 and dt_str.isdigit():
                            if dt_str < cutoff_str:
                                delete_url = f"{base_url}/{path_suffix}?op=DELETE&recursive=true"
                                print(f"Deleting expired HDFS partition: {base_url}/{path_suffix}")
                                del_resp = requests.delete(delete_url, timeout=15)
                                if del_resp.status_code == 200:
                                    print(f"Successfully deleted {path_suffix}")
                                else:
                                    print(f"Failed to delete {path_suffix}: {del_resp.text}")
            elif resp.status_code == 404:
                print(f"Directory not found (it might be empty or not created yet): {base_url}")
            else:
                print(f"Failed to list directory {base_url}: {resp.status_code} - {resp.text}")
        except Exception as e:
            print(f"Error during cleaning {base_url}: {e}")
