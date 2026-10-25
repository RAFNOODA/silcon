"""Historical technology progression and balancing data."""
from dataclasses import dataclass

@dataclass(frozen=True)
class Architecture:
    name: str
    year: int
    tier: int
    multiplier: float
    description: str

@dataclass(frozen=True)
class ProcessNode:
    name: str
    nm: int
    year: int
    tier: int
    cost_factor: float

@dataclass(frozen=True)
class Memory:
    name: str
    year: int
    tier: int
    multiplier: float
    cost_factor: float

ARCHITECTURES = [
    Architecture("3D Accelerator", 1998, 0, 1.00, "Sabit işlevli 3B hızlandırma"),
    Architecture("Transform & Lighting", 2001, 1, 1.28, "Geometri işlemleri GPU'ya taşınıyor"),
    Architecture("Programmable Shader", 2003, 2, 1.72, "Programlanabilir piksel ve vertex shader'ları"),
    Architecture("Unified Shader", 2007, 3, 2.40, "Birleşik ve esnek işlem kümeleri"),
    Architecture("Parallel Compute", 2012, 4, 3.35, "Grafik yanında genel amaçlı hesaplama"),
    Architecture("AI Accelerator", 2018, 5, 4.85, "Derin öğrenme ve matris hızlandırma"),
    Architecture("Chiplet GPU", 2022, 6, 6.20, "Modüler kalıp ve gelişmiş paketleme"),
    Architecture("Neural Render", 2025, 7, 7.65, "Yapay zekâ destekli görüntü üretimi"),
    Architecture("Optical Compute", 2029, 8, 9.40, "Deneysel fotonik yardımcı birimler"),
]

PROCESS_NODES = [
    ProcessNode("250 nm", 250, 1998, 0, 1.00),
    ProcessNode("180 nm", 180, 2000, 1, 0.92),
    ProcessNode("130 nm", 130, 2002, 2, 0.86),
    ProcessNode("90 nm", 90, 2004, 3, 0.82),
    ProcessNode("65 nm", 65, 2006, 4, 0.79),
    ProcessNode("40 nm", 40, 2009, 5, 0.74),
    ProcessNode("28 nm", 28, 2011, 6, 0.70),
    ProcessNode("16 nm", 16, 2015, 7, 0.64),
    ProcessNode("7 nm", 7, 2019, 8, 0.59),
    ProcessNode("5 nm", 5, 2021, 9, 0.55),
    ProcessNode("3 nm", 3, 2023, 10, 0.51),
    ProcessNode("2 nm", 2, 2026, 11, 0.47),
]

MEMORIES = [
    Memory("SDRAM", 1998, 0, 1.00, 1.00),
    Memory("DDR", 2001, 1, 1.12, 1.06),
    Memory("GDDR3", 2003, 2, 1.28, 1.12),
    Memory("GDDR5", 2008, 3, 1.58, 1.20),
    Memory("HBM", 2013, 4, 1.92, 1.52),
    Memory("GDDR6", 2018, 5, 2.05, 1.29),
    Memory("HBM2e", 2020, 6, 2.42, 1.68),
    Memory("GDDR7", 2024, 7, 2.72, 1.44),
    Memory("HBM4", 2026, 8, 3.20, 1.84),
]

COMPETITORS = [
    {"name": "Titan Systems", "focus": "Oyuncu", "score": 114, "price": 279},
    {"name": "RedPeak Graphics", "focus": "Performans", "score": 92, "price": 229},
    {"name": "Arcadia Labs", "focus": "Verimlilik", "score": 83, "price": 199},
    {"name": "Zenith Compute", "focus": "İş istasyonu", "score": 105, "price": 399},
]

MILESTONES = {
    1998: ("3B hızlandırma çağı", "Donanım tabanlı 3B hızlandırıcılar pazarı şekillendiriyor."),
    2001: ("Transform & Lighting", "Geometri hesapları GPU'ya taşınıyor; üst segmentte beklentiler artıyor."),
    2004: ("Programlanabilir shader", "Geliştiriciler GPU iş hattı üzerinde daha fazla kontrol istiyor."),
    2007: ("Birleşik shader mimarisi", "Esnek işlem birimleri performans rekabetini yeniden tanımlıyor."),
    2012: ("GPU hesaplama", "Paralel hesaplama, grafik dışındaki iş yüklerini de çekmeye başlıyor."),
    2016: ("Derin öğrenme dalgası", "Veri merkezi ve makine öğrenmesi pazarlarının önemi büyüyor."),
    2018: ("AI hızlandırma yarışı", "Matris birimleri ve yazılım ekosistemi rekabet avantajı yaratıyor."),
    2022: ("Chiplet ve paketleme", "Gelişmiş paketleme ve yüksek bant genişlikli bellek stratejik hale geliyor."),
    2025: ("Yapay zekâ destekli grafik", "Render kalitesi, bellek kapasitesi ve enerji verimliliği birlikte değerlendiriliyor."),
    2028: ("İleri üretim sınırları", "Yeni üretim düğümlerinin maliyeti artarken verimlilik daha önemli oluyor."),
    2032: ("Heterojen hesaplama", "Grafik, AI ve özel hızlandırıcılar daha sıkı biçimde bir araya geliyor."),
}

EVENTS = [
    {"title": "Wafer arzında daralma", "text": "Dökümhane kapasitesi sıkıştı. Üretim maliyetleri bu ay %12 yükseldi.", "kind": "cost", "value": 0.12},
    {"title": "Oyuncu pazarı canlandı", "text": "Yeni oyunlar tüketici GPU talebini artırdı. Bu ay satış potansiyeli %18 yüksek.", "kind": "demand", "value": 0.18},
    {"title": "Sürücü sorunu gündemde", "text": "Kullanıcılar kararlılık sorunlarından şikâyetçi. İtibarınız geçici olarak etkilenebilir.", "kind": "reputation", "value": -3},
    {"title": "Üretim verimi iyileşti", "text": "Tedarikçi süreci optimize etti. Üretim maliyetleri bu ay %8 düştü.", "kind": "discount", "value": 0.08},
    {"title": "AI yatırım dalgası", "text": "Kurumsal müşteriler hızlandırıcı arıyor. İş yükü talebi bu ay %22 arttı.", "kind": "demand", "value": 0.22},
    {"title": "Tüketici harcamaları yavaşladı", "text": "Makroekonomik belirsizlik orta segment satışlarını yavaşlattı.", "kind": "recession", "value": -0.12},
]
