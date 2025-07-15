# Fájlátviteli Rendszer

Egy Python alapú hálózati fájlátviteli rendszer, amely MD5 ellenőrzőösszegekkel validálja a fájlok integritását.

## Projekt Leírása

A rendszer három komponensből áll:

1. **checksum_srv.py** - Ellenőrzőösszeg szerver, amely tárolja és visszaadja a fájlok MD5 hash-eit lejárati idővel
2. **netcopy_cli.py** - Kliens, amely fájlokat küld a fájlszerverre és ellenőrzőösszegeket a checksum szerverre
3. **netcopy_srv.py** - Fájlszerver, amely fogadja a fájlokat és validálja őket a tárolt ellenőrzőösszegekkel

## Működés

1. A kliens kiszámolja a fájl MD5 ellenőrzőösszegét
2. A kliens elküldi a fájlt a fájlszerverre
3. A kliens elküldi az ellenőrzőösszegot a checksum szerverre lejárati idővel
4. A fájlszerver fogadja a fájlt és lekérdezi az ellenőrzőösszeget a checksum szervertől
5. A szerver kiírja "CSUM OK" ha helyes, vagy "CSUM CORRUPTED" ha sérült

## Használat

### 1. Ellenőrzőösszeg szerver indítása

```bash
python checksum_srv.py <ip> <port>
```

**Példa:**
```bash
python checksum_srv.py 127.0.0.1 8000
```

### 2. Fájlszerver indítása

```bash
python netcopy_srv.py <bind_ip> <bind_port> <chsum_ip> <chsum_port> <file_id> <output_file>
```

**Példa:**
```bash
python netcopy_srv.py 127.0.0.1 9000 127.0.0.1 8000 test_file received_file.txt
```

### 3. Fájl küldése klienssel

```bash
python netcopy_cli.py <srv_ip> <srv_port> <chsum_ip> <chsum_port> <file_id> <file_path>
```

**Példa:**
```bash
python netcopy_cli.py 127.0.0.1 9000 127.0.0.1 8000 test_file example.txt
```

## Teljes Példa

1. **Checksum szerver indítása:**
   ```bash
   python checksum_srv.py 127.0.0.1 8000
   ```

2. **Fájlszerver indítása (külön terminálban):**
   ```bash
   python netcopy_srv.py 127.0.0.1 9000 127.0.0.1 8000 my_file output.txt
   ```

3. **Fájl küldése (harmadik terminálban):**
   ```bash
   python netcopy_cli.py 127.0.0.1 9000 127.0.0.1 8000 my_file test.txt
   ```

## Követelmények

- Python 3.6+
- Szabványos Python könyvtárak (socket, hashlib, sys, os)

## Protokoll

### Checksum szerver parancsok:
- `BE|file_id|expiry|length|checksum` - Ellenőrzőösszeg tárolása
- `KI|file_id` - Ellenőrzőösszeg lekérése

### Válaszok:
- `OK` - Sikeres tárolás
- `length|checksum` - Ellenőrzőösszeg visszaadása
- `0|` - Nem található vagy lejárt
- `ERR` - Hiba

## Megjegyzések

- Az ellenőrzőösszegek alapértelmezett lejárata 60 másodperc
- A fájlok 4096 bájtos blokkokban kerülnek átvitelre
