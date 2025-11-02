import json, time, requests, os, sys

CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_config(cfg):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=4)

def check_balance(api_key):
    try:
        r = requests.get(f"https://api.dongvanfb.net/user/balance?apikey={api_key}", timeout=10).json()
        if r["error_code"] == 200:
            print(f"Số dư hiện tại: {r['balance']:,}")
            return True
        else:
            print("API key sai hoặc hết hạn.")
            return False
    except Exception as e:
        print("Lỗi khi kiểm tra balance:", e)
        return False

def clear_console():
    os.system('cls' if os.name == 'nt' else 'clear')

def show_account_types():
    mail_list = [
        {"id": 5, "name": "Hotmail TRUSTED [IMAP/POP3]", "price": 650},
        {"id": 6, "name": "Outlook TRUSTED [IMAP/POP3]", "price": 650},
        {"id": 1, "name": "HotMail NEW", "price": 50},
        {"id": 2, "name": "OutLook NEW", "price": 50},
        {"id": 3, "name": "OutLook DOMAIN NEW", "price": 50},
    ]
    print("\nDanh sách loại mail có thể mua:")
    for acc in mail_list:
        print(f"[{acc['id']}] {acc['name']} | Giá: {acc['price']}")
    return mail_list

def buy_mail(api_key, acc_id, quality, acc_type="full"):
    url = f"https://api.dongvanfb.net/user/buy?apikey={api_key}&account_type={acc_id}&quality={quality}&type={acc_type}"
    r = requests.get(url, timeout=15).json()
    if r["error_code"] == 200:
        print(f"\nMua thành công {quality} mail:")
        mails = r["data"]["list_data"]
        for i, entry in enumerate(mails, 1):
            print(f"{i}. {entry}")
        return mails
    else:
        print("Lỗi mua mail:", r.get("message"))
        return []

def parse_mail(entry):
    parts = entry.split("|")
    email = parts[0] if len(parts) > 0 else ""
    password = parts[1] if len(parts) > 1 else ""
    refresh_token = parts[2] if len(parts) > 2 else ""
    uuid = parts[-1] if len(parts) > 3 else ""
    return email, password, refresh_token, uuid

def get_code(email, refresh_token, client_id, check_type="facebook"):
    url = "https://tools.dongvanfb.net/api/get_code_oauth2"
    payload = {"email": email, "refresh_token": refresh_token, "client_id": client_id, "type": check_type}
    try:
        r = requests.post(url, json=payload, timeout=10).json()
        if r.get("status"):
            print(f"✅ Mail: {email}")
            print(f"→ Code: {r.get('code')}")
            print(f"→ Date: {r.get('date')}\n")
            return r.get("code")
    except Exception:
        pass
    return None

def select_platform():
    platforms = ["facebook", "instagram", "google", "tiktok", "twitter"]
    print("\nChọn nền tảng muốn lấy code:")
    for i, p in enumerate(platforms, 1):
        print(f"[{i}] {p}")
    while True:
        try:
            choice = int(input("Nhập số tương ứng: "))
            if 1 <= choice <= len(platforms):
                return platforms[choice - 1]
        except:
            pass
        print("Lựa chọn không hợp lệ, nhập lại.")

def main():
    while True:
        cfg = load_config()

        # ==== API KEY ====
        api_key = cfg.get("api_key")
        if not api_key:
            api_key = input("Nhập API key: ").strip()
            cfg["api_key"] = api_key
            save_config(cfg)
        else:
            print(f"\nAPI key hiện tại: {api_key}")
            ch = input("Nhấn [Enter] để dùng key cũ hoặc nhập key mới: ").strip()
            if ch:
                api_key = ch
                cfg["api_key"] = api_key
                save_config(cfg)

        if not check_balance(api_key):
            continue
        clear_console()
        # ==== LỰA CHỌN SETTING (gồm nền tảng) ====
        last_setting = cfg.get("last_setting")
        if last_setting:
            print("\nCấu hình trước:")
            print(json.dumps(last_setting, indent=4, ensure_ascii=False))
            use_old = input("Dùng cấu hình cũ? (y/n): ").lower().strip()
        else:
            use_old = "n"

        if use_old == "y":
            acc_id = last_setting["account_type"]
            qty = last_setting["quality"]
            platform = last_setting["platform"]
            clear_console()
            input("Cấu hình đã lưu. Nhấn [Enter] để bắt đầu...")
            clear_console()
        else:
            show_account_types()
            acc_id = input("\nNhập ID loại mail muốn mua: ").strip()
            qty = int(input("Nhập số lượng mail muốn mua: ").strip())
            clear_console()
            platform = select_platform()
            cfg["last_setting"] = {
                "account_type": acc_id,
                "quality": qty,
                "type": "full",
                "platform": platform
            }
            save_config(cfg)
            clear_console()
            input("Cấu hình đã lưu. Nhấn [Enter] để bắt đầu...")
            clear_console()

        # ==== MUA MAIL ====
        mails = buy_mail(api_key, acc_id, qty, "full")
        if not mails:
            continue

        # ==== CHECK CODE ====
        print(f"\nĐang đợi code ({platform}) từ các mail... (600 giây kiểm tra liên tục)")
        for entry in mails:
            email, pw, _, _ = parse_mail(entry)
            print(f"→ Theo dõi mail: {email} | Mật khẩu: {pw}")

        start = time.time()
        found = {}
        while time.time() - start < 600:
            for entry in mails:
                email, pw, token, client_id = parse_mail(entry)
                if email not in found:
                    code = get_code(email, token, client_id, check_type=platform)
                    if code:
                        found[email] = code
            if len(found) == len(mails):
                print("\nĐã nhận đủ code từ tất cả mail.")
                break
            time.sleep(5)

        print("\n--- Tổng kết ---")
        for entry in mails:
            email, pw, _, _ = parse_mail(entry)
            print(f"{email} ({pw}) → {found.get(email, 'Chưa có code')}")

        choice = input("\nNhấn [Enter] để quay lại menu chính, hoặc gõ bất kỳ phím nào khác để thoát: ").strip()
        clear_console()
        if choice != "":
            print("Đang thoát tool...")
            sys.exit(0)

if __name__ == "__main__":
    main()
