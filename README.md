# Silicon Foundry — GPU Company Simulator

Türkçe arayüzlü, dönem tabanlı bir donanım şirketi yönetim simülasyonu. 1998'de küçük bir ekran kartı girişimiyle başlar; teknoloji araştırır, GPU tasarlar, üretim kapasitesi planlar, fiyat belirler, personel alır ve büyüyen pazarda rekabet edersin.

> **Durum:** Oynanabilir ilk sürüm (v0.1.0). Teknoloji ve pazar dengesi bir simülasyon modelidir; ürün performansları ve rakip şirketler oyun için kurgulanmıştır. Tarih çizgisi, GPU endüstrisindeki gerçek teknoloji dönemlerinden esinlenir.

## Oyun özellikleri

- **GPU laboratuvarı:** Mimari, üretim düğümü, bellek ve saat hızını seçerek ürün tasarla.
- **Dönem ilerlemesi:** 1998'den başlayıp tarihsel teknoloji kilometre taşlarından esinlenen bir zaman çizgisinde aylık ilerle.
- **Fabrika ve üretim:** Kapasiteyi yükselt, ürün bazında üretim hedefleri ayarla, stok ve üretim maliyetini yönet.
- **Pazar yönetimi:** Ürün fiyatlarını değiştir, satışları ve hayali rakipleri karşılaştır.
- **AR-GE:** Mimari, üretim düğümü, bellek teknolojisi ve sürücü optimizasyonlarını araştır.
- **Şirket yönetimi:** Mühendis, araştırmacı ve pazarlamacı işe al; pazarlama bütçesi ve tek seferlik kampanyalar kullan.
- **Finans ve olaylar:** Aylık gelir/gider raporları, grafikler ve rastgele pazar olayları.
- **Kayıt sistemi:** Manuel kayıt ve ay ilerletirken otomatik kayıt.
- **Windows EXE:** GitHub Actions, Windows üzerinde bağımsız `SiliconFoundry.exe` dosyası üretir.

## Yerel çalıştırma

Python 3.12 önerilir.

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python main.py
```

Testleri çalıştır:

```bash
pip install -r requirements-dev.txt
python -m pytest -q
```

## GitHub Actions ile Windows EXE alma

1. Bu klasörün içindeki **tüm dosyaları** yeni bir GitHub deposuna yükle. `.github/workflows/build-windows.yml` dosyasının depoda bulunduğundan emin ol.
2. Depo **Settings → Actions → General** bölümünde Actions kullanımının etkin olduğundan emin ol.
3. Yerel Git ile ilk gönderim örneği (URL kısmını kendi deponla değiştir):

```bash
git init
git add .
git commit -m "Initial Silicon Foundry game"
git branch -M main
git remote add origin https://github.com/USERNAME/REPOSITORY.git
git push -u origin main
```

Mevcut bir depoya gönderiyorsan `git init` ve `git remote add origin ...` adımlarını tekrar yapma; değişiklikleri `git add .`, `git commit -m "Build Silicon Foundry game"` ve `git push` ile gönder.

4. GitHub deposunda **Actions → Build Windows EXE** akışının tamamlanmasını bekle.
5. Başarılı çalıştırmayı aç, sayfanın altındaki **Artifacts → SiliconFoundry-Windows** öğesini indir ve ZIP içinden `SiliconFoundry.exe` dosyasını çıkar.

Workflow, Windows runner üzerinde testleri çalıştırır ve PyInstaller ile tek dosyalı GUI EXE oluşturur. EXE bu ortamda önceden derlenmez; GitHub Actions'ın Windows makinesinde derlenir.

## Kayıt konumu

- Windows: `%APPDATA%\SiliconFoundry\save.json`
- Linux: `~/.local/share/silicon-foundry/save.json`

## Proje yapısı

```text
silicon-foundry/
├── .github/workflows/build-windows.yml  # Windows EXE build workflow
├── gpu_tycoon/
│   ├── app.py                            # Pygame interface and input
│   ├── data.py                           # Technology timeline and market data
│   ├── economy.py                        # Simulation, economy and saving
│   ├── models.py                         # Company and product data models
│   └── ui.py                             # Reusable UI drawing primitives
├── tests/test_economy.py                 # Core simulation tests
├── main.py                               # App entry point
├── requirements.txt
└── requirements-dev.txt
```

## Troubleshooting

- **EXE doesn't start / missing DLL:** Download the artifact ZIP, extract the EXE to a writable folder and try again. Windows SmartScreen may warn about unsigned self-built executables; this project does not sign the EXE.
- **Actions failed:** Open the failed job log and inspect the first error. The workflow uses Python 3.12, installs the dependencies, runs tests, then packages the game.
- **Save won't load:** A corrupt JSON save can be renamed or removed from the save location. A fresh game creates a new save on the first month advance.

## License

MIT. See `LICENSE`.
