
# WSL / Docker guide — kjøre ROS Jazzy og PiCam-containere

Denne korte guiden viser hvordan du raskt kjører ROS 2 (Jazzy) i WSL2 eller Docker på din maskin, og hvordan du kjører PiCam-serveren eller PiCam-capture i containere slik at de kan kommunisere med Raspberry Pi-en.

Viktige prinsipper
- Bruk samme ROS 2-distribusjon på begge maskiner (her: `jazzy`).
- Sett `FASTDDS_BUILTIN_TRANSPORTS=UDPv4` i begge miljø for stabil DDS-over-UDP.
- Bruk samme `ROS_DOMAIN_ID` hvis du vil isolere kommunikasjonen.
- Pi og PC må være på samme nettverk (ikke NAT som blokkerer UDP).

Forutsetninger
- WSL2 med Ubuntu (eller Linux-maskin) eller Docker Desktop på Windows.
- Docker installert og WSL-integrasjon aktivert hvis du bruker Docker Desktop.

1) Bygg og kjør PiCam-server (kjør på PC eller i WSL)

Bygg et kortvarig containermiljø og kjør `app_detect.py` direkte fra `picam_server`-mappen:

```bash
# Fra repo-rot
cd picam_server
docker pull ros:jazzy-ros-base
docker run -it --rm --network host \
  -e FASTDDS_BUILTIN_TRANSPORTS=UDPv4 \
  -e ROS_DOMAIN_ID=0 \
  -v "$(pwd)":/app -w /app \
  ros:jazzy-ros-base bash -c \
  "pip3 install --break-system-packages --no-cache-dir flask opencv-python-headless numpy onnxruntime && python3 app_detect.py"
```

Notater:
- `--network host` er viktig for pålitelig DDS-discovery når du tester lokalt.
- Bruk `opencv-python-headless` i containere for å unngå GUI-avhengigheter.

2) Bygg og kjør Pi-side capture container (på Raspberry Pi)

Hvis du vil kjøre `picamThread.py` i en container på Pi-en, bygg Docker-imaget fra `picam_server/Dockerfile` og start det med privilegert tilgang:

```bash
# På Raspberry Pi (repo tilgjengelig på Pi)
cd /path/to/repo
docker build -f picam_server/Dockerfile -t picam_thread:jazzy .
docker run -d --name roverpi-picam_thread --privileged --network host \
  -e FASTDDS_BUILTIN_TRANSPORTS=UDPv4 -e ROS_DOMAIN_ID=0 \
  -v "$(pwd)/picam_server":/app -w /app \
  --device /dev/video0:/dev/video0 \
  picam_thread:jazzy
```

Notater for Pi:
- `--privileged` og `--device` trengs for å gi container tilgang til kamera og libcamera.
- Alternativt kan du kjøre `python3 picamThread.py` direkte i en ROS2-enabled virtuell miljø hvis du foretrekker det.

3) Kjør i WSL uten Docker (kort)

Hvis du vil bruke WSL direkte (ingen Docker), installer ROS Jazzy i WSL/Ubuntu, aktivér ROS 2-miljøet, og kjør:

```bash
# I WSL/Ubuntu
source /opt/ros/jazzy/setup.bash
export FASTDDS_BUILTIN_TRANSPORTS=UDPv4
export ROS_DOMAIN_ID=0
cd /mnt/c/Users/<you>/.../picam_server
pip3 install --user --break-system-packages flask opencv-python numpy onnxruntime
python3 app_detect.py
```

Feilsøkingstips
- Hvis du ikke ser ROS-topic fra Pi: sjekk brannmur, samme nettverk, og at `FASTDDS_BUILTIN_TRANSPORTS` er satt.
- Bruk `ros2 topic echo /picam/captured_image` for å verifisere at compressed-image-meldinger kommer gjennom.
- Sett `ROS_DOMAIN_ID` lik på begge sider for å unngå kryss-snakk med andre ROS-nettverk.

Sikkerhet og ytelse
- `--privileged` gir vid tilgang; bruk kun på betrodde enheter (Pi).
- For produksjon kan det være bedre å kjøre tjenestene direkte på Pi uten container eller sette opp et mer begrenset container-runtime.

Vil du at jeg legger en kort `docker-compose`- eksempel for kjøring av `app_detect` i en container på PC-en? (Jeg kan lage en liten `docker-compose.server.yml` ferdig konfigurert.)
