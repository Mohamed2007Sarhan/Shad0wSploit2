import argparse
import json
import traceback
from datetime import datetime
import zoneinfo

def main():
    parser = argparse.ArgumentParser(description="Get current time, optionally for a specific timezone.")
    parser.add_argument("--timezone", type=str, default="UTC", help="Timezone name (e.g., 'America/New_York', 'UTC')")
    args = parser.parse_args()

    try:
        if args.timezone:
            tz = zoneinfo.ZoneInfo(args.timezone)
        else:
            tz = zoneinfo.ZoneInfo("UTC")
            
        current_time = datetime.now(tz)
        
        result = {
            "status": "success",
            "timezone": args.timezone,
            "time": current_time.isoformat(),
            "formatted": current_time.strftime("%Y-%m-%d %H:%M:%S %Z%z")
        }
        print(json.dumps(result))
    except Exception as e:
        error_result = {
            "status": "error",
            "message": str(e),
            "traceback": traceback.format_exc()
        }
        print(json.dumps(error_result))

if __name__ == "__main__":
    main()
