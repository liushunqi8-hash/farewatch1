# farewatch ✈️

Set a target price for the routes you care about. Get notified the moment a fare drops below it.

为你在乎的航线设一个心理价位，票价跌破就第一时间通知你。

## Features | 功能

- 🎯 Target-price alerts per route/date — 按航线/日期设目标价，跌破才提醒
- 📅 Explicit dates or auto-scanned date ranges — 支持指定日期或按区间自动扫描
- 🔌 Amadeus Self-Service API (free tier) — 免费 API 查价
- 📲 Notifications: console, [Bark](https://bark.day.app) (iOS), [ServerChan](https://sct.ftqq.com) (WeChat) — 多种推送方式
- 🧠 Alert-once state: the same drop never notifies you twice — 同一低价只提醒一次
- 🧪 `mock` provider for demos — no API key needed to try it

## Quickstart | 快速开始

```bash
pip install -r requirements.txt
# or install the `farewatch` command: pip install .
cp config.example.yaml config.yaml
# edit config.yaml: routes, target prices, notifier keys
# 填写你的航线、目标价和推送 key

# demo mode (no API key needed | 无需 key 直接试)
python -m farewatch check --config config.mock.yaml --dry-run

# real check (needs Amadeus keys | 需要 Amadeus key)
export AMADEUS_CLIENT_ID=xxx AMADEUS_CLIENT_SECRET=xxx
python -m farewatch check
```

Get free Amadeus API keys at https://developers.amadeus.com/ (Self-Service, free tier).
Amadeus 免费 key 申请地址同上（Self-Service 免费档）。

Run it on a schedule with cron (macOS/Linux) — 挂到定时任务每天自动跑：

```cron
0 8 * * * cd /path/to/farewatch && python -m farewatch check --config config.yaml
```

## Config | 配置说明

```yaml
provider: amadeus  # amadeus | mock

amadeus:
  client_id: "${AMADEUS_CLIENT_ID}"
  client_secret: "${AMADEUS_CLIENT_SECRET}"
  hostname: "test"  # test | production

routes:
  - origin: WUH
    destination: CDG
    departure_dates: ["2027-03-08"]   # explicit dates | 指定日期
    target_price: 1500
    currency: CNY
  - origin: WUH
    destination: LIS
    date_range:                        # or scan a range | 或按区间扫描
      start: "2027-05-01"
      end: "2027-05-31"
      step_days: 7
    target_price: 1500
    currency: CNY

notifiers:
  - type: bark
    key: "${BARK_KEY}"
```

## Notes | 说明

- The Amadeus **test** environment returns sample data — great for trying things out. For real fares, switch `hostname` to `production` (requires Amadeus approval).
  Amadeus 的 test 环境返回的是示例数据，适合试玩；要查真实票价请切到 production（需官方审核）。
- Prices are snapshots, not bookings. Always confirm on the airline/OTA before paying.
  查到的是快照价不是下单价，下单前请以航司/OTA 实际价格为准。

## License

MIT
