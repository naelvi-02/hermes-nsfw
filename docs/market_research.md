# Market Research & Pricing Analysis
## AI Companion Bot — Indo Market

---

## 1. Kompetitor Global (Benchmark)

| Platform | Free | Basic | Premium | Notes |
|---|---|---|---|---|
| **Character.AI** | Ya (limited) | $9.99/mo | — | Paling viral, 20M+ DAU |
| **Janitor AI** | Ya (pakai API key sendiri) | — | — | NSFW, tapi pakai API user |
| **SpicyChat** | Ya (limited) | ~$9.99/mo | ~$19.99/mo | NSFW, ada image gen |
| **Replika** | Ya (SFW) | $7.99/mo | $14.99/mo | Companion focused |
| **Crushon AI** | Ya (25 msg/day) | $4.9/mo | $9.9/mo | NSFW chat |
| **Venus AI** | Ya | $9.99/mo | — | NSFW |

**Takeaway:**
- Range harga global: **$5–$20/bulan** (~Rp 80rb–320rb)
- Free tier selalu ada, biasanya 20–50 msg/day
- NSFW = premium feature standar di semua platform
- **Video generation = belum ada** di hampir semua. Ini gap nyata.

---

## 2. Konteks Indo Market

### Daya Beli
- UMR Jakarta 2025: ~Rp 5.3 juta/bulan
- Budget digital per bulan kelas menengah indo: Rp 50rb–200rb
- Netflix Basic (tanpa iklan) di Indo: Rp 65.000/bulan
- Spotify Premium Indo: Rp 54.990/bulan
- Referensi psikologis: **"under Rp 50rb"** terasa murah, **Rp 100rb+** perlu justifikasi value

### Platform Digital Indo
- Pengguna Telegram Indo: sangat aktif, terutama komunitas tech, adult content, RP
- NSFW Telegram bot: sudah ada pasar, tapi kebanyakan pakai bot sederhana tanpa AI companion experience
- Payment: **QRIS dan transfer bank** paling familiar. Kartu kredit minoritas.

### Kompetitor Lokal Relevan
- Tidak ada AI companion NSFW lokal yang signifikan (gap pasar nyata)
- Ada beberapa bot Telegram NSFW sederhana tapi tidak AI-powered
- JanitorAI dan SpicyChat ada userbase indo tapi bahasa Inggris semua

---

## 3. Biaya Infra Per User Per Bulan

### Asumsi volume: 100 user aktif

#### Free Tier (LLM saja)
| Komponen | Detail | Cost/user/bulan |
|---|---|---|
| Chat LLM | `deepseek/deepseek-chat-v3-0324:free` via OpenRouter | **$0** |
| Image SFW | Perchance API | **$0** |
| VPS share | 100 user, VPS $24/bulan | ~$0.24 |
| **Total FREE** | | **~$0.24/user** |

#### PRO Tier
| Komponen | Detail | Cost/user/bulan |
|---|---|---|
| Chat LLM | Hanami `sao10k/l3.1-70b-hanami-x1` via OpenRouter | ~$0.50–1.50 (tergantung volume) |
| Image NSFW | Novita ~$0.004/image × 30 img/bulan | ~$0.12 |
| VPS share | | ~$0.24 |
| **Total PRO** | | **~$0.86–1.86/user** |

> **Catatan Novita**: Harga per image ~$0.003–0.006 tergantung model. 50 img/day limit = max $9/user/bulan kalau dipakai semua. Perlu soft cap **30–50 img/bulan** untuk PRO, bukan per-hari, lebih fleksibel.

#### ULTRA Tier
| Komponen | Detail | Cost/user/bulan |
|---|---|---|
| Semua PRO | | ~$1.86 |
| Video (Modal L4) | 30 video × $0.06/video | ~$1.80 |
| **Total ULTRA** | | **~$3.66/user** |

### Modal Video Cost Detail
```
L4 GPU: $0.000222/sec
+ 2 CPU core: $0.0000131 × 2 / sec = $0.0000262/sec  
+ 16GB RAM: $0.00000222 × 16 / sec = $0.0000355/sec
Total/sec: ~$0.000294/sec

Render time per video (4-step, 24 frame, 512px): ~60–90 detik
Cost per video: ~$0.018–0.027 (warm run)
Dengan cold start buffer (~30 detik): ~$0.026–0.035
Safe estimate: $0.04–0.06/video
```

---

## 4. Payment Gateway — Perbandingan

### Opsi untuk Indo Market

| | **Tripay** | **Midtrans** | **Telegram Stars** |
|---|---|---|---|
| Setup | Mudah, bisa indie | Perlu PT/CV | Native, sangat mudah |
| Fee QRIS | 0.7% | 0.7% | ~30% (Telegram cut) |
| Fee Transfer | Rp 1.500–2.500 flat | Rp 4.000 | — |
| Familiar user | ✅ Sangat | ✅ Sangat | ❌ Asing di Indo |
| Butuh PT/CV | ❌ Tidak | ✅ Ya | ❌ Tidak |
| Webhook | ✅ | ✅ | ✅ |
| Daftar | Mudah, cukup KTP | Susah | Via bot settings |
| **Verdict** | **✅ Pilihan utama** | Nanti | Sekunder |

**Tripay** = pilihan terbaik untuk MVP Indo. Fee kecil, bisa daftar sebagai individu, support QRIS + VA + e-wallet.

> Pakasir lebih ke POS system untuk warung/coffee shop, bukan payment gateway untuk digital product. **Kurang tepat untuk use case ini.**

---

## 5. Rekomendasi Pricing Final

### Tier Structure

```
┌─────────────────────────────────────────────────────┐
│  FREE                                    Rp 0/bulan │
│  • Chat SFW (DeepSeek/Groq, model gratis)           │
│  • Image SFW via Perchance (unlimited)              │
│  • Limit: 30 pesan/hari                             │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  PRO                               Rp 29.000/bulan  │
│  • Chat NSFW unlimited (Hanami)                     │
│  • Image NSFW via Novita (30 img/bulan)             │
│  • Prioritas response                               │
└─────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────┐
│  ULTRA                             Rp 59.000/bulan  │
│  • Semua PRO                                        │
│  • Image NSFW unlimited (50 img/bulan)              │
│  • 20 video credit/bulan                            │
│  • Beli video credit tambahan: Rp 5.000/5 video    │
└─────────────────────────────────────────────────────┘
```

### Kenapa Angka Ini?

| Tier | Revenue | HPP | Margin |
|---|---|---|---|
| FREE | Rp 0 | ~Rp 3.800 | — (akuisisi) |
| PRO | Rp 29.000 | ~Rp 14.000–18.000 | ~40–50% |
| ULTRA | Rp 59.000 | ~Rp 38.000–45.000 | ~25–40% |

- PRO di bawah Rp 30rb → impulse purchase territory
- ULTRA di bawah Rp 60rb → masih "worth it" dibanding Netflix
- Margin PRO paling sehat karena LLM cost per-token di Hanami relatif kecil untuk conversation normal

### Credit Tambahan Video
```
Pack A: 5 video = Rp 5.000
Pack B: 20 video = Rp 15.000 (Rp 750/video)
Pack C: 50 video = Rp 30.000 (Rp 600/video)

HPP per video: ~Rp 640–960 ($0.04–0.06)
Jual Pack A: Rp 1.000/video → margin tipis, tapi OK
Jual Pack B: Rp 750/video → impas atau sedikit margin
Jual Pack C: Rp 600/video → rugi kalau cold start sering
```

> ⚠️ Video credit pricing perlu direvisi setelah ada data real render time dari Modal.
> Saranku: **mulai Pack A dan B saja**, Pack C nanti setelah cost lebih terkontrol.

---

## 6. Break-even & Target Revenue

### Skenario 100 User Aktif
```
Asumsi distribusi:
  60 Free + 30 PRO + 10 ULTRA

Revenue:
  PRO:   30 × Rp 29.000 = Rp 870.000
  ULTRA: 10 × Rp 59.000 = Rp 590.000
  Total: Rp 1.460.000/bulan

HPP:
  Free:  60 × Rp 3.800  = Rp 228.000
  PRO:   30 × Rp 18.000 = Rp 540.000
  ULTRA: 10 × Rp 45.000 = Rp 450.000
  VPS:   Rp 360.000 (Linode 8GB $24)
  Total HPP: Rp 1.578.000

Profit: -Rp 118.000 (hampir BEP)
```

### BEP Sederhana
```
Dengan 40 PRO + 15 ULTRA dari 200 user:
  Revenue: 40×29k + 15×59k = Rp 2.045.000
  HPP est: ~Rp 1.800.000
  → mulai profit
```

**Kesimpulan: BEP di sekitar 30–40 PRO user + 10–15 ULTRA user.**
Realistis dicapai dalam 2–3 bulan dengan marketing aktif di komunitas Telegram Indo.

---

## 7. Risiko & Mitigasi

| Risiko | Dampak | Mitigasi |
|---|---|---|
| Novita cost overrun (image abuse) | Tinggi | Hard limit 30 img/bulan PRO, 50 ULTRA |
| Modal cold start sering | Sedang | Cache model, queue worker |
| User indo tidak mau bayar | Sedang | Free tier harus cukup addictive |
| Ban Telegram bot | Tinggi | Grup privat, bukan public, ToS hati-hati |
| OpenRouter rate limit | Rendah | Fallback model |
