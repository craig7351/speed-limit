# Windows Speed Limit (Windows 11 全域頻寬限制器)

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Platform](https://img.shields.io/badge/Platform-Windows%2011-orange)
![License](https://img.shields.io/badge/License-MIT-green)

這是一個基於 Python 與 `pydivert` (WinDivert) 的 Windows 原生網路頻寬限制工具。
不同於 Windows 內建的 QoS 原則（通常僅支援上傳限制），本工具能夠達到**全域下載 (Inbound)** 與 **全域上傳 (Outbound)** 的雙向流量控制。

## ✨ 功能特色

*   **全域頻寬限制**: 針對整台電腦的網路流量進行整形 (Traffic Shaping)。
*   **雙向控制**: 支援獨立設定 **下載** 與 **上傳** 的 Mbps 速限。
*   **不需重啟**: 即時生效，隨開隨用。
*   **圖形化介面**: 提供簡單易用的 GUI 操作。

## 🛠️ 技術原理

本專案使用 **Token Bucket (權杖桶)** 演算法來進行流量整形。
*   **核心驅動**: 使用 `pydivert` 攔截 Windows 網路堆疊 (Network Stack) 中的封包。
*   **運作機制**: 程式會攔截所有 IP 封包，計算當前流量消耗。如果超過設定的頻寬限制，程式會計算即時延遲 (Latency) 並暫停封包的發送，從而達到限制網速的效果。

## 📦 安裝與使用

### 前置需求
*   Windows 10 / 11 (需管理員權限)
*   Python 3.8 或以上版本

### 安裝步驟

1.  複製專案到本地：
    ```bash
    git clone https://github.com/yourusername/speed-limit.git
    cd speed-limit
    ```

2.  安裝依賴：
    ```bash
    pip install -r requirements.txt
    ```
    *(主要依賴 `pydivert`，程式啟動時會嘗試自動安裝)*

### 🚀 如何執行

請直接執行目錄下的批次檔：

*   **啟動**: 雙擊 `start.bat`
    *   會跳出使用者帳戶控制 (UAC) 請求權限，請點選「是」。
    *   視窗開啟後，輸入欲限制的 Mbps 數值 (例如 `5` 代表 5 Mbps)，點擊 **START Limiting**。
*   **停止**: 雙擊 `stop.bat` 或在程式介面點擊 **STOP** (或直接關閉視窗)。

## ⚠️ 注意事項

*   **防毒軟體**: 由於本程式使用 `WinDivert` 驅動攔截封包，部分防毒軟體可能會將其誤判為風險程式。如遇此情況，請將程式加入白名單。
*   **網路中斷**: 若程式在執行中意外崩潰 (Crash)，網路可能會暫時中斷。此時只需重新執行程式並正常關閉，或直接重啟電腦即可恢復。

## 📂 檔案結構

*   `main.py`: GUI 主程式與權限管理。
*   `traffic_shaper.py`: 核心流量整形邏輯 (Token Bucket 演算法)。
*   `start.bat`: 方便的一鍵啟動腳本。
*   `stop.bat`: 緊急停止/清理腳本。

## 📝 License

[MIT License](LICENSE)
