https://www.virtualbox.org/wiki/Downloads?utm_source=chatgpt.com



VirtualBox는 Windows에 “가상 컴퓨터(가상 머신)”를 만드는 프로그램이에요. 지금 목표(쿠버네티스 멀티노드 VM 3대)라면 VirtualBox를 먼저 설치하고, Host-Only 네트워크(vboxnet0) 를 만들어야 합니다.

아래대로 그대로 따라 하시면 됩니다.

1) VirtualBox 다운로드/설치 (Windows 10 Home)
다운로드

공식 다운로드 페이지에서 Windows hosts 설치 파일을 받습니다. 
VirtualBox
+1

설치(중요 포인트)

설치 파일 실행

중간에 네트워크 드라이버/어댑터 설치 관련 안내가 뜨면 허용(Install) 하세요

설치가 끝나면(필요 시) 재부팅

Host-Only 어댑터가 안 생기는 대부분의 이유가 “네트워크 구성요소(드라이버) 설치가 제대로 안 됨”입니다.

2) Host-Only 네트워크(vboxnet0) 만들기

VirtualBox 실행 →
File → Tools → Network Manager → Host-only Networks 탭 → Create

VirtualBox 매뉴얼에도 이 경로(File → Tools → Network Manager)가 나옵니다. 
VirtualBox

권장 설정:

IPv4 Address: 192.168.56.1

IPv4 Mask: 255.255.255.0

DHCP: 끄기(OFF) (우리는 VM에서 정적 IP 쓸 예정)

3) Windows에서 Host-Only 어댑터가 생겼는지 확인

PowerShell:

ipconfig | findstr /i "VirtualBox"


정상이면 VirtualBox Host-Only Network 같은 항목이 보이고,
IPv4가 192.168.56.1처럼 나와야 합니다.

지금 사용자는 그 항목이 없었으니(= 아직 Host-Only가 없음), 위 2번이 반드시 필요합니다.

4) 만약 Create 했는데도 어댑터가 안 생기면 (빠른 해결)

가장 빠른 방법은 VirtualBox 설치 “Repair(복구)” 입니다.

설치 파일 다시 실행 → Repair 선택 → 재부팅
(Host-Only 드라이버가 꼬인 케이스에서 흔히 해결됩니다—커뮤니티에서도 이슈/해결 사례가 있습니다.) 
VirtualBox 포럼
+2
VirtualBox 포럼
+2

5) 그 다음 단계(미리 안내)

Host-Only가 생기면, 각 VM(cp1/w1/w2)에:

Adapter 1: NAT

Adapter 2: Host-Only(vboxnet0)
를 붙이고, Ubuntu에서 192.168.56.10/11/12로 IP를 잡아 멀티노드 K3s를 구성합니다.

지금 바로 할 것

VirtualBox 설치했나요? (아직이면 설치부터)

설치 후 File → Tools → Network Manager에서 Host-Only Create 해보세요.

그리고 다시 PowerShell에서:

ipconfig | findstr /i "VirtualBox"


출력 결과를 그대로 붙여주시면, 다음 단계(각 VM 네트워크/고정 IP)로 바로 이어서 진행해드릴게요.

9s 동안 생각함

지금 올려주신 화면은 VirtualBox “관리자(Manager)” 첫 실행 화면이에요. 여기서 다음 단계는 2가지입니다:

Host-Only 네트워크(vboxnet0) 만들기

VM(cp1/w1/w2) 3대 생성할 때 Adapter 2에 vboxnet0 붙이기

아래 순서대로 그대로 따라 하시면 됩니다.

1) (지금 화면) Basic/Expert Mode는 아무거나 OK

오른쪽에 보이는 Basic Mode / Expert Mode 중

그냥 Basic Mode 눌러도 되고

저는 옵션이 더 잘 보이는 Expert Mode를 추천합니다.

2) Host-Only 네트워크(vboxnet0) 만들기
방법 A (가장 흔한 경로)

상단 메뉴에서:

파일(F) → 도구(Tools) → Network Manager(네트워크 관리자)
또는
파일(F) → Host Network Manager(호스트 네트워크 관리자)

들어가면 “Host-only Networks(호스트 전용 네트워크)” 같은 탭이 있어요.

거기서:

Create(생성) 클릭

아래처럼 설정(권장)

IPv4 Address: 192.168.56.1

IPv4 Mask: 255.255.255.0

DHCP Server: OFF(끔) ← (우리는 VM에서 정적 IP 쓸 거라 꺼두는 게 편함)

생성되면 이름이 보통 vboxnet0로 잡힙니다.

방법 B (Tools 메뉴가 안 보일 때)

상단 툴바의 “환경 설정(P)”(Preferences) 들어가서
Network(네트워크) / Host-only Networks 쪽에서 생성하는 메뉴가 있는 경우도 있어요.

3) Windows에서 Host-Only 어댑터가 생겼는지 확인

PowerShell에서:

ipconfig | findstr /i "VirtualBox"


정상이면 아래 같은 항목이 새로 생깁니다:

VirtualBox Host-Only Network

IPv4: 192.168.56.1

✅ 이게 보여야 192.168.56.10(cp1) 같은 VM IP 대역이 “진짜로” 살아납니다.

4) (다음 단계 미리) VM 3대 네트워크는 이렇게 붙이면 됨

각 VM(cp1/w1/w2) 설정 → Network

Adapter 1: NAT

Adapter 2: Host-only Adapter → Name: vboxnet0 → Cable connected 체크

지금 바로 해볼 것 (한 번만)

Network Manager / Host Network Manager 들어가서 vboxnet0 생성

생성 후 PowerShell에서 ipconfig | findstr /i "VirtualBox" 결과를 붙여주세요.

그러면 제가 바로 이어서:

cp1/w1/w2 VM에 Adapter2 붙이는 화면 위치

Ubuntu 22.04에서 192.168.56.10/11/12 고정 IP 잡는 netplan

K3s 멀티노드 조인
까지 막힘 없이 다음 단계로 딱 이어드릴게요.

파일 - 도구 - 네트워크관리자 없음

오케이. 지금 UI(스크린샷) 보니까 VirtualBox 버전에 따라 “도구(Tools)” 메뉴가 숨겨져 있거나 한국어 UI에서 명칭이 조금 달라서 안 보이는 케이스예요. 그래도 Host-Only(vboxnet0)는 반드시 만들 수 있습니다. 아래 순서대로 해보세요(위에서부터 1번이 제일 확실).

1) “환경 설정(P)”에서 Host-Only 만들기 (가장 흔한 대체 경로)

상단 툴바에 “환경 설정(P)”(렌치+드라이버 아이콘) 있죠?

환경 설정(P) 클릭

왼쪽에서 네트워크(Network) 또는 네트워크 선택

탭 중에 Host-only Networks / 호스트 전용 네트워크 또는 Host Network Manager 같은 항목이 있어요

거기서 추가(+) / Create 눌러서 생성

생성 후 값 확인

IPv4: 192.168.56.1

Mask: 255.255.255.0

DHCP: OFF(끔) (정적 IP 쓸 거라 추천)

UI에 “Host-only”라는 단어가 반드시 있습니다.

2) “파일(F) → 환경 설정(Preferences)” 경로도 확인

메뉴바에서:

파일(F) → 환경 설정(P)

여기서도 1번과 같은 화면으로 들어갑니다.

3) 그래도 안 보이면: “Host Network Manager” 메뉴명이 다른 경우

버전에 따라 메뉴명이 아래처럼 나옵니다(비슷한 의미):

호스트 네트워크 관리자

호스트 전용 네트워크

네트워크

네트워크 관리

Host Network Manager

Host-only Networks

환경설정 화면에서 “네트워크” 쪽만 찾으면 됩니다.

4) (최후수단) VBoxManage로 Host-Only 생성 (GUI 없이도 가능)

만약 GUI에서 진짜 못 찾겠으면, Windows CMD/PowerShell에서 VirtualBox CLI로 생성할 수 있어요.

PowerShell:

"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" list hostonlyifs


없으면 생성:

"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" hostonlyif create


IP 설정:

"C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" hostonlyif ipconfig "VirtualBox Host-Only Ethernet Adapter" --ip 192.168.56.1 --netmask 255.255.255.0


(어댑터 이름이 다르면 list hostonlyifs 출력의 이름을 그대로 넣으면 됩니다.)

5) 생성 확인(제일 중요)

Host-Only 만들고 나서 PowerShell에서:

ipconfig | findstr /i "VirtualBox"


여기에 VirtualBox Host-Only 어댑터가 나타나야 성공입니다.

지금 당장 제일 빠른 다음 액션

상단의 환경 설정(P) 버튼 클릭 → 네트워크 메뉴 찾기

거기에 Host-Only(호스트 전용) 추가/생성 버튼 있는지 확인

가능하면 환경 설정(P) 화면 스샷 한 장만 올려주세요.
(네트워크 항목이 보이게) 그러면 제가 그 화면 기준으로 “어디 눌러야 하는지” 바로 찍어서 안내해드릴게요.

16s 동안 생각함

지금 올려주신 화면은 **“새 VM 만들기 마법사”**라서, 여기엔 네트워크 관리자 메뉴가 안 보이는 게 정상이에요.
Host-Only(vboxnet0)는 ‘전역 설정(환경 설정)’에서 만드는 게 맞습니다. (스크린샷에 상단 환경 설정(P) 아이콘이 보이네요.)

아래대로 해보세요.

1) 먼저 이 “새 VM 만들기” 창은 닫기

오른쪽 아래 취소(C) 눌러서 창을 닫고, VirtualBox 메인 화면으로 돌아가세요.

2) Host-Only(vboxnet0) 만들기 (현재 화면 기준 가장 확실한 경로)

메인 화면 상단에 있는 환경 설정(P)(렌치 아이콘) 클릭

환경 설정(P) 클릭

왼쪽 메뉴에서 네트워크(Network) 찾기

위쪽 탭에서 Host-only Networks / 호스트 전용 네트워크(또는 “호스트 전용”) 탭 선택

오른쪽에 추가(+) / Create 버튼 눌러 생성

생성된 항목 선택 후 값 확인/수정

IPv4 Address: 192.168.56.1

IPv4 Mask: 255.255.255.0

DHCP: 끔(OFF) (정적 IP 쓸 거라 추천)

“네트워크(Network)” 메뉴만 찾으면 됩니다. “도구→네트워크 관리자”가 없어도 이 경로로 만들 수 있어요.

3) Windows에서 생성 확인

PowerShell에서:

ipconfig | findstr /i "VirtualBox"


여기에 VirtualBox Host-Only 어댑터가 뜨고 IPv4가 192.168.56.1이면 성공입니다.

4) 그 다음(중요): VM 3대에 Host-Only 붙이기

VM 하나 만들고 나서도 됩니다.

각 VM 설정 → 네트워크

어댑터 1: NAT

어댑터 2: 호스트 전용 어댑터(Host-only) → 이름 vboxnet0 선택 → 케이블 연결됨 체크

만약 “환경 설정(P) → 네트워크” 자체가 안 보이면

그건 설치가 꼬여서 Host-Only 드라이버가 빠진 경우라, VirtualBox 설치 파일로 Repair(복구) 하면 바로 잡히는 경우가 많아요.

원하시면 제가 정확히 찍어서 안내할게요:
환경 설정(P) 창을 열고, 왼쪽 메뉴가 보이게 스크린샷 한 장만 더 올려주세요(네트워크 항목 찾는 용도).

네트워크가 안보임
12s 동안 생각함

스크린샷 상태를 보면 Preferences가 “Basic(기본)” 모드라서 항목이 일부만 보이는 상태예요. 그래서 “네트워크”가 안 뜹니다.

1) 제일 먼저: Basic → Expert로 바꾸기

지금 창 상단에 Basic / Expert 탭이 있죠?

➡️ Expert를 클릭하세요.
그러면 왼쪽 메뉴에 보통 네트워크(Network) 항목이 추가로 나타납니다.

2) 검색으로 바로 찾기(더 빠름)

오른쪽 위 Search settings에 아래 중 하나를 입력해보세요.

network

host-only

네트워크

검색하면 관련 설정으로 바로 점프하거나, 숨겨진 카테고리가 표시됩니다.

3) Expert로 바꿔도 “네트워크”가 계속 없으면(중요)

이 경우는 거의 VirtualBox 설치할 때 “Networking 기능/드라이버”가 빠졌거나 설치가 꼬인 상태입니다.
(그래서 Host-Only 어댑터도 Windows ipconfig에 안 보였던 상황과 딱 맞습니다.)

✅ 해결: VirtualBox 설치 파일 다시 실행 → Repair(복구) 또는 재설치

VirtualBox 설치 파일(.exe) 다시 실행

Repair(복구) 선택 (없으면 제거 후 재설치)

설치 옵션에서 Networking 관련 구성요소가 체크되어 있는지 확인

설치 중 “드라이버 설치” 경고가 뜨면 무조건 허용/설치

끝나면 재부팅(요구 시)

복구 후 PowerShell에서 이걸로 확인:

ipconfig | findstr /i "VirtualBox"


여기에 VirtualBox Host-Only 어댑터가 뜨면 성공입니다.

지금 바로 할 것

Preferences 창에서 Expert 클릭해보시고

그래도 없으면, VirtualBox 설치 파일로 Repair 진행

Expert로 바꾼 화면에서 왼쪽 메뉴가 보이게 한 장만 더 캡처 올려주시면, 제가 “어디에 Host-only 생성 버튼이 있는지” 정확히 찍어서 이어서 안내할게요.

expert 에도 네트워크 안보임

좋아요. 이 화면이면 정상 케이스가 아닙니다.
Expert인데도 왼쪽에 네트워크(Network) 항목이 “통째로” 없고, 아래에 **“잘못된 설정 감지됨”**까지 뜨는 걸 보면:

✅ VirtualBox의 Host-Only/Networking 구성요소(드라이버)가 설치가 안 됐거나 깨진 상태일 가능성이 매우 높습니다.
그래서 Windows ipconfig에도 “VirtualBox Host-Only” 어댑터가 안 보였던 거고요.

지금은 GUI에서 해결하려고 해도 계속 막힐 확률이 높아서, 아래 2단계로 바로 복구하는 게 가장 빠릅니다.

1) (1분 진단) VBoxManage로 Host-Only 목록 확인

PowerShell에서(그대로 복붙):

& "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" list hostonlyifs


아무것도 안 나오거나 에러면 → 드라이버/네트워크 기능이 깨짐 확정.

2) (권장/정석) VirtualBox “Repair(복구)” 실행

VirtualBox 설치 파일(.exe) 다시 실행

Repair(복구) 선택

설치 중 “드라이버 설치” 창이 뜨면 무조건 Install(설치)

끝나면 재부팅(요구되면 꼭)

Windows 10에서 네트워크 드라이버가 막히면 Host-Only가 생성 자체가 안 됩니다.

복구 후 확인:

ipconfig | findstr /i "VirtualBox"


여기서 VirtualBox Host-Only Network가 떠야 정상입니다.

3) Repair 후에도 안 되면 (거의 확실한 해결 루트)
A) 완전 제거 → 재설치

“앱 및 기능”에서 VirtualBox 제거

재부팅

최신 VirtualBox 재설치 (설치 중 드라이버 허용)

B) Windows 방해 요소 체크(가끔 원인)

회사 PC 보안(드라이버 설치 차단)

백신/보안 프로그램이 VirtualBox 네트워크 드라이버 설치 차단

4) (복구 성공 후) Host-Only 생성 (CLI로 바로 가능)

Repair 후에 아래로 vboxnet0 생성까지 한 번에 가능합니다.

& "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" hostonlyif create
& "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" list hostonlyifs


생성된 어댑터 이름이 나오면(예: VirtualBox Host-Only Ethernet Adapter), IP 설정:

& "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" hostonlyif ipconfig "VirtualBox Host-Only Ethernet Adapter" --ip 192.168.56.1 --netmask 255.255.255.0


그리고 다시 확인:

ipconfig | findstr /i "VirtualBox"

지금 당장 한 가지 선택해서 진행

위의 VBoxManage.exe list hostonlyifs를 실행한 결과를 붙여주거나

바로 VirtualBox 설치 파일로 Repair 진행

저는 2) Repair가 가장 빠르다고 봅니다.
Repair 끝나고 ipconfig | findstr /i "VirtualBox" 결과만 보여주시면, 그 다음 단계(각 VM에 Adapter2=vboxnet0 붙이고 192.168.56.10/11/12 고정 IP)로 바로 이어갈게요.

PS C:\Users\LG> & "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe" list hostonlyifs
Name:            VirtualBox Host-Only Ethernet Adapter
GUID:            26028e7b-6442-4a9b-96d1-c7b7195dc5bc
DHCP:            Disabled
IPAddress:       192.168.56.1
NetworkMask:     255.255.255.0
IPV6Address:     fe80::d646:ff67:ba60:1348
IPV6NetworkMaskPrefixLength: 64
HardwareAddress: 0a:00:27:00:00:3b
MediumType:      Ethernet
Wireless:        No
Status:          Up
VBoxNetworkName: HostInterfaceNetworking-VirtualBox Host-Only Ethernet Adapter

좋아요! ✅ 이 출력이면 Host-Only(vboxnet0 역할) 는 정상적으로 만들어져 있고, IP도 192.168.56.1로 살아있습니다.
(즉, GUI에서 “네트워크”가 안 보이는 건 UI 이슈/제한일 수 있지만, 기능은 이미 준비 완료)

이제 해야 할 건 3가지입니다.

1) Windows에서 Host-Only 어댑터가 보이는지 확인

PowerShell:

ipconfig | findstr /i "VirtualBox"


여기서 192.168.56.1이 보이면 OK.

2) cp1/w1/w2 VM에 “Host-Only Adapter” 붙이기 (핵심)

VirtualBox에서 VM 하나씩 들어가서 설정합니다.

(1) VM 선택 → 설정(Settings) → 네트워크(Network)

어댑터 1: NAT (그대로)

어댑터 2: ✅ 사용(Enable) 체크

연결 방식(Attached to): Host-only Adapter

이름(Name): VirtualBox Host-Only Ethernet Adapter (방금 출력에 나온 이름)

✅ 케이블 연결됨(Cable connected) 체크

GUI에 vboxnet0가 안 보일 수 있어도, 이름이 이렇게 뜨는 형태로 선택 가능합니다.

3) Ubuntu VM 안에서 192.168.56.10/11/12 고정 IP 잡기

VM에 Adapter2 붙인 뒤, Ubuntu에서 ip -br a로 인터페이스 확인하세요. (보통 enp0s8)

cp1 (192.168.56.10)
sudo tee /etc/netplan/00-installer-config.yaml >/dev/null <<'EOF'
network:
  version: 2
  ethernets:
    enp0s3:
      dhcp4: true
    enp0s8:
      dhcp4: no
      addresses: [192.168.56.10/24]
EOF
sudo netplan apply
ip -br a

w1 (192.168.56.11), w2 (192.168.56.12)

위에서 주소만 각각 바꿔서 적용.

4) 통신 테스트 (여기서 성공해야 K3S_URL이 의미가 있음)
Windows → cp1
ping 192.168.56.10

cp1 → Windows(Host-Only)
ping -c 1 192.168.56.1


✅ 여기까지 되면, 이제 워커 조인도 VM에서만 정상적으로 됩니다.

다음 단계(바로 이어서)

cp1에 k3s server 설치

cp1에서 토큰 확인

w1/w2에서 join

딱 한 줄만 확인해 주세요

지금 Windows에서 아래가 성공하나요?

ping 192.168.56.1


그리고 cp1 VM에 Adapter2 붙인 다음 ip -br a 출력도 한 번만 보내주면, 제가 당신 화면 기준으로 “어느 값을 K3S_URL에 넣는지”까지 정확히 마무리해드릴게요.

PS C:\Users\LG> ipconfig | findstr /i "VirtualBox"
PS C:\Users\LG>
25s 동안 생각함

오케이, 이 상황이 딱 “VirtualBox 쪽(VBoxManage)엔 Host-Only가 존재하는데, Windows 네트워크 어댑터로는 안 잡히는” 케이스예요.

즉:

VBoxManage list hostonlyifs ✅ → VirtualBox 내부 설정엔 “Host-Only 어댑터”가 있음

ipconfig ❌ → Windows에 실제 NDIS 어댑터가 안 생겼거나/숨김/비활성/드라이버 바인딩 깨짐

아래 순서대로 확인하면 원인이 바로 갈립니다.

1) PowerShell에서 “어댑터가 존재하는지” 먼저 찾기 (ipconfig보다 확실)

PowerShell에서 그대로 실행:

Get-NetAdapter -IncludeHidden | Sort-Object Name | Format-Table -Auto Name, Status, InterfaceDescription


그리고 VirtualBox 관련만 필터:

Get-NetAdapter -IncludeHidden | ? { $_.Name -match "VirtualBox|Host" -or $_.InterfaceDescription -match "VirtualBox" } |
  Format-Table -Auto Name, Status, InterfaceDescription

결과 해석

✅ 여기서 VirtualBox Host-Only… 가 보이면 → “비활성/숨김”일 가능성 큼 → 2번으로

❌ 아예 안 보이면 → “드라이버/구성요소가 Windows에 설치 안 됨” → 4번(Repair)로 직행

2) 네트워크 연결 창에서 확인/활성화

실행창(Win+R)에서:

ncpa.cpl


여기서 VirtualBox Host-Only… 어댑터가 보이는지 확인하고:

사용 안 함(Disabled) 이면 → 우클릭 → 사용(Enable)

보이는데도 ip가 없으면 → 우클릭 → 속성에서 Internet Protocol Version 4 (TCP/IPv4) 체크 확인

3) “숨김 장치”로 잡혀있는지(Device Manager)

Win+R:

devmgmt.msc


보기(View) → 숨김 장치 표시(Show hidden devices)

네트워크 어댑터(Network adapters)에서
VirtualBox Host-Only Ethernet Adapter 또는 VirtualBox 관련 항목 찾기

있는데 회색/비활성이라면:

우클릭 → 사용
또는 문제가 있으면:

우클릭 → 디바이스 제거(드라이버 포함 체크가 나오면 체크) → 재부팅 → 4번 Repair

4) 가장 확실한 해결: VirtualBox “Repair(복구)”

Windows에 어댑터가 안 보이는 경우는 이게 제일 빠릅니다.

VirtualBox 설치 파일(.exe) 다시 실행

Repair(복구)

중간에 드라이버 설치/보안 경고 뜨면 반드시 설치 허용

재부팅

끝나고 다시 확인:

ipconfig


또는

Get-NetAdapter | ? {$_.Name -match "VirtualBox"}

5) 참고: 지금 ipconfig | findstr가 안 찍힌 이유

ipconfig는 “어댑터 이름 줄”에 VirtualBox가 포함될 때만 필터링이 되는데, 현재는 아예 어댑터가 OS에 안 잡혀있거나 숨김/비활성이라 출력이 없었던 겁니다.

지금 제일 빠른 다음 스텝

위 1번 명령 실행 결과 중 VirtualBox 관련 라인만 복사해서 붙여주세요:

Get-NetAdapter -IncludeHidden | ? { $_.Name -match "VirtualBox|Host" -or $_.InterfaceDescription -match "VirtualBox" } |
  Format-Table -Auto Name, Status, InterfaceDescription


그 결과를 보면 (A) Enable만 하면 되는지 / (B) Repair로 가야 하는지 제가 바로 확정해서 다음 단계(Host-Only에 VM 붙이기 → 192.168.56.10/11/12)로 이어줄게요.

PS C:\Users\LG> Get-NetAdapter -IncludeHidden | Sort-Object Name | Format-Table -Auto Name, Status, InterfaceDescription


Name                                  Status       InterfaceDescription
----                                  ------       --------------------
6to4 Adapter                          Not Present
Bluetooth 네트워크 연결 2             Disconnected Bluetooth Device (Personal Area Network) #2
Microsoft IP-HTTPS Platform Interface Not Present
Teredo Tunneling Pseudo-Interface     Not Present
vEthernet (WSL (Hyper-V firewall))    Up           Hyper-V Virtual Ethernet Adapter
vSwitch (WSL (Hyper-V firewall))      Up           Hyper-V Virtual Switch Extension Adapter
Wi-Fi 2                               Up           Intel(R) Wi-Fi 6 AX201 160MHz #2
로컬 영역 연결* 11                    Disconnected Microsoft Wi-Fi Direct Virtual Adapter #3
로컬 영역 연결* 12                    Disconnected Microsoft Wi-Fi Direct Virtual Adapter #4
로컬 영역 연결* 2                     Disconnected WAN Miniport (SSTP)
로컬 영역 연결* 3                     Disconnected WAN Miniport (IKEv2)
로컬 영역 연결* 4                     Disconnected WAN Miniport (L2TP)
로컬 영역 연결* 5                     Disconnected WAN Miniport (PPTP)
로컬 영역 연결* 6                     Disconnected WAN Miniport (PPPOE)
로컬 영역 연결* 7                     Up           WAN Miniport (IP)
로컬 영역 연결* 8                     Up           WAN Miniport (IPv6)
로컬 영역 연결* 9                     Up           WAN Miniport (Network Monitor)
이더넷                                Up           VirtualBox Host-Only Ethernet Adapter
이더넷(커널 디버거)                   Not Present  Microsoft Kernel Debug Network Adapter

좋습니다. ✅ Windows에 Host-Only 어댑터가 “이더넷 / VirtualBox Host-Only Ethernet Adapter”로 정상 존재합니다.
findstr "VirtualBox"가 안 찍힌 건 “이름이 VirtualBox가 아니라 ‘이더넷’”이라서 그래요(설명(InterfaceDescription)에만 VirtualBox가 들어있음).

이제 남은 건 IP가 192.168.56.1로 잡혀있는지 확인하고, VM에 Adapter2로 붙인 뒤 192.168.56.10/11/12를 잡으면 끝입니다.

1) Windows Host-Only IP가 192.168.56.1인지 확인

PowerShell:

Get-NetIPAddress -InterfaceAlias "이더넷" -AddressFamily IPv4


여기서 IPAddress : 192.168.56.1 이면 OK

만약 다른 값이거나 비어있으면, 강제로 세팅(안전):

New-NetIPAddress -InterfaceAlias "이더넷" -IPAddress 192.168.56.1 -PrefixLength 24


(이미 있으면 에러 날 수 있는데, 그럼 기존 IP를 알려주시면 거기에 맞춰 조정할게요.)

2) Windows ↔ Host-Only 자체 통신 체크
ping 192.168.56.1


이건 당연히 자기 자신이라 응답 나와야 합니다.

3) 이제 VM에 Host-Only(Adapter2) 붙이기

각 VM(cp1/w1/w2) 설정 → Network

Adapter 1: NAT

Adapter 2: Enable

Attached to: Host-only Adapter

Name: VirtualBox Host-Only Ethernet Adapter

Cable connected 체크

4) Ubuntu VM에서 Host-Only IP 잡기

cp1에서:

ip -br a


Host-Only NIC(보통 enp0s8) 확인 후 netplan 설정:

cp1 (192.168.56.10)
sudo tee /etc/netplan/00-installer-config.yaml >/dev/null <<'EOF'
network:
  version: 2
  ethernets:
    enp0s3:
      dhcp4: true
    enp0s8:
      dhcp4: no
      addresses: [192.168.56.10/24]
EOF
sudo netplan apply
ip -br a


w1/w2는 주소만 192.168.56.11, 192.168.56.12로 변경.

5) 가장 중요한 테스트: Windows → cp1 ping

VM 설정 + netplan 적용 후 Windows에서:

ping 192.168.56.10


✅ 이게 성공하면, 드디어 K3S_URL="https://192.168.56.10:6443"로 멀티노드 조인이 “정상 루트”로 됩니다.

지금 다음으로 할 일

Get-NetIPAddress -InterfaceAlias "이더넷" -AddressFamily IPv4 결과(IPv4가 뭔지)

cp1 VM에 Adapter2 붙인 뒤 ip -br a 결과

이 두 개만 주시면, 바로 이어서 K3s 서버 설치 + w1/w2 조인까지 한 번에 마무리 명령으로 연결해드릴게요.

PS C:\Users\LG> Get-NetIPAddress -InterfaceAlias "이더넷" -AddressFamily IPv4


IPAddress         : 192.168.56.1
InterfaceIndex    : 59
InterfaceAlias    : 이더넷
AddressFamily     : IPv4
Type              : Unicast
PrefixLength      : 24
PrefixOrigin      : Manual
SuffixOrigin      : Manual
AddressState      : Preferred
ValidLifetime     :
PreferredLifetime :
SkipAsSource      : False
PolicyStore       : ActiveStore

완벽합니다. ✅ Windows Host-Only 어댑터가 192.168.56.1/24로 정상 세팅됐어요.

이제 남은 건 VM 3대(cp1/w1/w2)에 Host-Only(어댑터2) 붙이고, Ubuntu에서 192.168.56.10/11/12 고정 IP를 잡은 뒤 K3s 멀티노드 설치하면 끝입니다.

1) VirtualBox에서 VM 네트워크 설정 (3대 모두)

각 VM 선택 → 설정(Settings) → 네트워크(Network)

어댑터 1: NAT

어댑터 2: 사용(Enable) 체크

연결 방식: Host-only Adapter

이름: VirtualBox Host-Only Ethernet Adapter

✅ 케이블 연결됨(Cable connected)

이 설정을 해야 VM끼리 + Windows와 192.168.56.x로 통신됩니다.

2) Ubuntu 22.04에서 Host-Only 고정 IP 설정 (각 VM)

각 VM에서 먼저 인터페이스 이름 확인:

ip -br a


보통

NAT: enp0s3

Host-Only: enp0s8

cp1: 192.168.56.10
sudo tee /etc/netplan/00-installer-config.yaml >/dev/null <<'EOF'
network:
  version: 2
  ethernets:
    enp0s3:
      dhcp4: true
    enp0s8:
      dhcp4: no
      addresses: [192.168.56.10/24]
EOF
sudo netplan apply
ip -br a

w1: 192.168.56.11 / w2: 192.168.56.12

주소만 각각 바꿔서 동일하게 적용하세요.

3) 통신 테스트 (여기서 성공해야 다음으로 진행)
Windows → cp1

PowerShell:

ping 192.168.56.10

cp1 → Windows Host-Only

cp1에서:

ping -c 1 192.168.56.1


✅ 둘 다 되면 네트워크 완료.

4) K3s 멀티노드 설치 (Docker 없이)
4-1) hostname 유니크 (각 VM에서 1회)
sudo hostnamectl set-hostname cp1   # cp1
sudo hostnamectl set-hostname w1    # w1
sudo hostnamectl set-hostname w2    # w2

4-2) cp1에 서버 설치

cp1에서:

sudo apt update && sudo apt install -y curl

curl -sfL https://get.k3s.io | \
  K3S_KUBECONFIG_MODE="644" sh -s - \
  --node-ip 192.168.56.10 \
  --flannel-iface enp0s8


토큰 확인:

sudo cat /var/lib/rancher/k3s/server/node-token

4-3) w1/w2 워커 조인 (WSL 말고 “VM 콘솔”에서!)

w1에서:

sudo apt update && sudo apt install -y curl

curl -sfL https://get.k3s.io | \
  K3S_URL="https://192.168.56.10:6443" \
  K3S_TOKEN="(cp1에서 복사한 토큰)" sh -s - \
  --node-ip 192.168.56.11 \
  --flannel-iface enp0s8


w2에서(주소만 변경):

sudo apt update && sudo apt install -y curl

curl -sfL https://get.k3s.io | \
  K3S_URL="https://192.168.56.10:6443" \
  K3S_TOKEN="(토큰)" sh -s - \
  --node-ip 192.168.56.12 \
  --flannel-iface enp0s8

4-4) cp1에서 최종 확인
kubectl get nodes -o wide
kubectl get pods -A


cp1, w1, w2가 Ready면 성공.

중요 정리

WSL은 워커로 조인하지 마세요. (WSL ↔ Host-Only 네트워크가 기본으로 직접 통신 안 되는 경우가 많아서 이미 한 번 막혔죠.)

WSL은 필요하면 나중에 kubectl 관리용으로만 붙이면 됩니다.

지금 다음 액션

cp1 VM에 어댑터2 붙인 뒤, cp1에서 ip -br a 출력 한 줄만 보내주세요.

그리고 Windows에서 ping 192.168.56.10 결과도 알려주세요.

그 두 개가 OK면, 제가 당신 환경 기준으로 **정확한 인터페이스 이름(enp0s8 맞는지)**까지 포함해서 “완전 복붙” 최종 커맨드로 마무리해드릴게요.


#############################
![alt text](image.png)

https://releases.ubuntu.com/jammy/
![alt text](image-1.png)

![alt text](image-2.png)