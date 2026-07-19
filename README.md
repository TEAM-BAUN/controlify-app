# Controlify

Aynı ağdaki bilgisayarlar arasında **sunucusuz (P2P)** uzaktan ekran paylaşımı,
kontrol ve dosya transferi uygulaması. PySide6 (Qt 6) + stdlib soketleri.

## İndirme

Hazır binary'ler (Windows / macOS / Linux) [Releases](../../releases)
sayfasından indirilebilir. Kaynak koddan çalıştırmak için aşağıya bakın.

## Nasıl çalışır?

- Her istemci açılışta LAN'a UDP broadcast ile kendini duyurur; "Aktif
  Bilgisayarlarım" listesi bu duyurulardan beslenir. Sunucu, kayıt, internet
  bağlantısı gerekmez.
- Bağlantı kurulunca iki istemci arasında doğrudan TCP oturumu açılır: ekran
  görüntüleri (JPEG), mouse olayları ve dosya parçaları bu tek bağlantı
  üzerinden length-prefixed binary protokolle akar.

## Gereksinimler

- [uv](https://docs.astral.sh/uv/) (bağımlılıkları ve Python sürümünü otomatik yönetir)

## Kullanımı

```bash
uv run app.py
```

İlk çalıştırmada uv gerekli Python sürümünü ve tüm bağımlılıkları (PySide6,
mss, pynput) otomatik kurar.

Aynı LAN'daki iki bilgisayarda uygulamayı açın; ID'ler listede belirir,
çift tıklayıp "Bağlan" ile oturum başlatın.

> macOS'ta ekran kaydı ve mouse kontrolü için Sistem Ayarları'ndan
> "Ekran Kaydı" ve "Erişilebilirlik" izinleri gerekir.

## Test

```bash
uv run python tests/test_network.py
```

## Binary derleme

```bash
uv run pyinstaller controlify.spec
```

Çıktı `dist/` altına düşer. `v*` etiketi push'lanınca GitHub Actions üç
platform için binary derleyip Release'e ekler.

## Notlar

- Keşif UDP 54545 portunu kullanır; oturum portu işletim sisteminden dinamik alınır.
- Bağlantılar şifresiz ve kimlik doğrulamasızdır — yalnızca güvendiğiniz
  yerel ağlarda kullanın.

## Geliştirenler

- Ahmet Yusuf Başaran
- Yusufcan Günay
