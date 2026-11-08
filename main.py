import os, sys, time, base64, random, json, codecs, string, re, hmac, hashlib
import threading, requests, urllib3
from datetime import datetime
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from flask import Flask, request, Response, send_from_directory
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============ CONFIG ============
ACCOUNTS_FILE = "accounts.json"
API_HEX_KEY    = "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"
API_SECRET_KEY = "2ee44819e9b4598845141067b281621874d0d5d7af9d8f7e00c1e54715b7d1e3"
AES_KEY_G = bytes([89,103,38,116,99,37,68,69,117,104,54,37,90,99,94,56])
AES_IV_G  = bytes([54,111,121,90,68,114,50,50,69,51,121,99,104,106,77,37])

REGION_LANG = {"BD":"bn","IND":"hi","PK":"ur","SG":"en","ID":"id","ME":"ar","VN":"vi","TW":"zh","CIS":"ru","TH":"th","EU":"en","US":"en","SAC":"es","LK":"en"}

# ============ BIO (Watermark) ============
BIO_TEXT = "[B][C][FF0000]@ViRtU4Lios [C][00FFFF]| [C][FFD700]Made by proxy [C][00FF00]| [C][FFFFFF]ViRtU4Lios BOT"

DATADOME_CID = "FWTNdJThVpQebS2UwFDDVuTDUrooDRONkwc3RotkozZEl36Ud9amFYFASlPQMF~5P0rgDg1HOU~kVRzCxF6SzKLxq~n1woK49aR5JKDK6WeO1sPcQ1W41MJLWf0MurjT"
DATADOME_DDK = "AE3F04AD3F0D3A462481A337485081"

LOCK = threading.Lock()

# ============ PROTOBUF ============
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\ndata.proto\"\xbb\x01\n\x04\x44\x61ta\x12\x0f\n\x07\x66ield_2\x18\x02 \x01(\x05\x12\x1e\n\x07\x66ield_5\x18\x05 \x01(\x0b\x32\r.EmptyMessage\x12\x1e\n\x07\x66ield_6\x18\x06 \x01(\x0b\x32\r.EmptyMessage\x12\x0f\n\x07\x66ield_8\x18\x08 \x01(\t\x12\x0f\n\x07\x66ield_9\x18\t \x01(\x05\x12\x1f\n\x08\x66ield_11\x18\x0b \x01(\x0b\x32\r.EmptyMessage\x12\x1f\n\x08\x66ield_12\x18\x0c \x01(\x0b\x32\r.EmptyMessage\"\x0e\n\x0c\x45mptyMessageb\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'data_pb2', _globals)

if _descriptor._USE_C_DESCRIPTORS == False:
    DESCRIPTOR._options = None
    _globals['_DATA']._serialized_start = 15
    _globals['_DATA']._serialized_end = 202
    _globals['_EMPTYMESSAGE']._serialized_start = 204
    _globals['_EMPTYMESSAGE']._serialized_end = 218

Data = _sym_db.GetSymbol('Data')
EmptyMessage = _sym_db.GetSymbol('EmptyMessage')

# ============ HELPERS ============
def encode_varint(n):
    if n < 0: return b''
    result = []
    while True:
        byte = n & 0x7F
        n >>= 7
        if n: byte |= 0x80
        result.append(byte)
        if not n: break
    return bytes(result)

def create_proto_field(field_num, value):
    if isinstance(value, int):
        return encode_varint((field_num << 3) | 0) + encode_varint(value)
    elif isinstance(value, (str, bytes)):
        ev = value.encode() if isinstance(value, str) else value
        return encode_varint((field_num << 3) | 2) + encode_varint(len(ev)) + ev
    return b''

def build_proto(fields):
    return b''.join(create_proto_field(k, v) for k, v in fields.items())

def encrypt_api(plain_hex):
    cipher = AES.new(AES_KEY_G, AES.MODE_CBC, AES_IV_G)
    return cipher.encrypt(pad(bytes.fromhex(plain_hex), AES.block_size)).hex()

def generate_password():
    return f"ViRtU4Lios_{''.join(random.choices(string.ascii_uppercase + string.digits, k=6))}"

def get_datadome_cookie():
    try:
        url = "https://api-sdk.datadome.co/sdk/"
        payload = {
            'cid': DATADOME_CID, 'ddv': "1.13.9", 'ddvc': "4.0.42", 'ddk': DATADOME_DDK,
            'request': "https://100067.connect.garena.com/api/v2/oauth/guest:register",
            'os': "Android", 'osr': "15", 'osn': "VANILLA_ICE_CREAM", 'osv': "35",
            'ua': "GarenaMSDK/4.0.42(25028RN03A ;Android 15;ar;EG;app 1.128.2 2019120828;)",
            'screen_x': "1640", 'screen_y': "720", 'screen_d': "320",
            'events': '[{"id":1,"message":"response validation","source":"sdk","date":' + str(int(time.time()*1000)) + '}]',
            'camera': '{"auth":"false","info":"{}"}',
            'mdl': "25028RN03A", 'prd': "serenity_global", 'mnf': "Xiaomi",
            'dev': "serenity", 'hrd': "serenity",
            'fgp': "Redmi/serenity_global/serenity:15/AP3A.240905.015.A2/A15.0.26.0.VGWMIXM:user/release-keys",
            'tgs': "release-keys", 'inte': "android-java-okhttp"
        }
        r = requests.post(url, data=payload, headers={'User-Agent':"okhttp/4.12.0",'Accept-Encoding':"gzip"}, timeout=15, verify=False)
        try:
            js = r.json()
            m = re.search(r'datadome=([^;]+)', js.get("cookie",""))
            if m: return m.group(1)
        except: pass
        c = r.cookies.get("datadome")
        if c: return c
        m = re.search(r'datadome=([^;]+)', r.headers.get("Set-Cookie",""))
        if m: return m.group(1)
    except Exception as e:
        print(f"[datadome] error: {e}")
    return None


# ============ MAJOR LOGIN ============
def major_login(access_token, open_id, lang):
    try:
        dT = bytes.fromhex('1a13323032362d30392d32382031363a33333a3039220966726565206669726528013a07312e3133322e38423e416e64726f6964204f53203135202f204150492d33352028415033412e3234303930352e3031352e41322f4131352e302e32362e302e5647574d49584d294a0848616e6468656c6452094d544e2053595249415a1243617272696572446174614e6574776f726b60e80c68d00572033332307a1d41524d3634204650204153494d4420414553207c2031383230207c20388001d21d8a01084d616c692d47353792013e4f70656e474c20455320332e322076312e72343970312d3034656163302e63383264376466616662353534653435316437303436356139613231666139389a012b476f6f676c657c34383535623136372d616539622d346237622d393531642d353234636336343461313962a2010c34362e35382e3137312e3639aa01026172b201203435393935623533323538333730306231393264643965356261646335316539ba010134c2010848616e6468656c64ca01115869616f6d69203235303238524e303341d201024d45ea014032383438303866316233326531653538343861303464666163303735633462633439613637613938646539303731356462343265313461316134666539663566f00101ca02094d544e205359524941d202023347ca03206538396231353865346263663938386562643039656238336635333738653837e00387df06e803cac701f003a50a8004cac801880487df069004cac801980487df06c80403d2045a2f646174612f6170702f7e7e35745f77707645586d6e3153656d6a757853337251673d3d2f636f6d2e6474732e667265656669726574682d56386e6233734e7a4b4a696a707a75737a55784c78773d3d2f6c69622f61726d3634e00401ea047a62386530636435653239356565653432663538363064336338366534383364647c2f646174612f6170702f7e7e35745f77707645586d6e3153656d6a757853337251673d3d2f636f6d2e6474732e667265656669726574682d56386e6233734e7a4b4a696a707a75737a55784c78773d3d2f626173652e61706bf00403f804028a050236349a050a32303139313231323239b205094f70656e474c455332b805ff3fc00504e0059b9501ea0507616e64726f6964f205704b717348547943694835645553466250354270506a44536e4f7235426652544d57323133433177397558326553476f6b317756356970464777385175503238326266496971724f4676364746766c4341794941384336787236483474316d35394933664e6153666f4466563435425748f805e7e40682062d7b226375725f72617465223a5b36302c39302c3132305d2c22737570706f72745f65746332223a66616c73657d8806019006019a060134a2060134b206094352171554095b5434c006f87bc80601d2068a0168747470733a2f2f646c2e616b2e66726565666972656d6f62696c652e636f6d2f6c6976652f4142486f74557064617465732f7c68747470733a2f2f636f72652d616b2e66726565666972656d6f62696c652e636f6d2f6c6976652f4142486f74557064617465732f7c3231316339333331363866353539303263376466626664386334653239353764da0612312e34323762356638316437323161343430')
        dT = dT.replace(b'2026-06-29 13:42:51', str(datetime.now())[:-7].encode())
        dT = dT.replace(b'284808f1b32e1e5848a04dfac075c4bc49a67a98de90715db42e14a1a4fe9f5f', access_token.encode())
        dT = dT.replace(b'45995b532583700b192dd9e5badc51e9', open_id.encode())
        data = bytes.fromhex(encrypt_api(dT.hex()))

        r = requests.post("https://loginbp.ppmainecoonghj.com/MajorLogin", headers={
            'User-Agent': "UnityPlayer/2018.4.12f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
            'Accept-Encoding': "deflate, gzip",
            'X-GA-SV': str(int(time.time())),
            'Authorization': "Bearer",
            'X-GA': "v1 1",
            'ReleaseVersion': "OB55",
            'Content-Type': "application/x-www-form-urlencoded",
            'X-Unity-Version': "2018.4.12f1"
        }, data=data, verify=False, timeout=20)

        print(f"[major_login] status={r.status_code} len={len(r.text)}")

        if r.status_code != 200:
            print(f"[major_login] FAIL body: {r.text[:200]}")
            return None

        jwt_start = r.text.find("eyJ")
        if jwt_start == -1:
            print(f"[major_login] no JWT in body: {r.text[:200]}")
            return None

        jwt_token = r.text[jwt_start:]
        second_dot = jwt_token.find(".", jwt_token.find(".") + 1)
        if second_dot == -1:
            print("[major_login] malformed JWT")
            return None

        jwt_token = jwt_token[:second_dot + 44]
        try:
            payload_part = jwt_token.split('.')[1]
            data_json = json.loads(base64.urlsafe_b64decode(payload_part + '=' * (4 - len(payload_part) % 4)))
            acc_id = data_json.get('account_id') or data_json.get('external_id')
            if acc_id:
                print(f"[major_login] OK account_id={acc_id}")
                return {"account_id": str(acc_id), "jwt_token": jwt_token}
            else:
                print(f"[major_login] JWT has no account_id: {list(data_json.keys())}")
        except Exception as e:
            print(f"[major_login] decode error: {e}")
    except Exception as e:
        print(f"[major_login] exception: {e}")
    return None


def set_account_bio(jwt_token, bio_text):
    import sys
    print(f"[bio] START jwt={'YES' if jwt_token else 'NO'} len={len(jwt_token) if jwt_token else 0}", flush=True, file=sys.stderr)
    
    if not jwt_token or len(jwt_token) < 50:
        print(f"[bio] ABORT: jwt_token invalid/empty", flush=True, file=sys.stderr)
        return False
    
    try:
        data = Data()
        data.field_2 = 17
        data.field_5.CopyFrom(EmptyMessage())
        data.field_6.CopyFrom(EmptyMessage())
        data.field_8 = bio_text
        data.field_9 = 1
        data.field_11.CopyFrom(EmptyMessage())
        data.field_12.CopyFrom(EmptyMessage())
        enc = AES.new(AES_KEY_G, AES.MODE_CBC, AES_IV_G).encrypt(pad(data.SerializeToString(), AES.block_size))
        
        print(f"[bio] sending request... enc_len={len(enc)}", flush=True, file=sys.stderr)
        
        r = requests.post("https://clientbp.ppmainecoonghj.com/UpdateSocialBasicInfo", headers={
            "User-Agent": "UnityPlayer/2018.4.12f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
            "Accept-Encoding": "deflate, gzip", "X-GA-SV": "1789535861",
            "Authorization": f"Bearer {jwt_token}", "X-GA": "v1 1",
            "ReleaseVersion": "OB55", "Content-Type": "application/x-www-form-urlencoded",
            "X-Unity-Version": "2018.4.12f1", "Host": "clientbp.ppmainecoonghj.com",
        }, data=enc, timeout=20, verify=False)
        
        print(f"[bio] RESPONSE status={r.status_code} len={len(r.text)} body={r.text[:200]}", flush=True, file=sys.stderr)
        return r.status_code == 200
    except Exception as e:
        print(f"[bio] EXCEPTION: {type(e).__name__}: {e}", flush=True, file=sys.stderr)
        return False


# ============ CREATE ACCOUNT ============
def create_account(region, prefix):
    max_attempts = 3
    for attempt in range(max_attempts):
        try:
            print(f"[attempt {attempt+1}] starting...")
            password = generate_password()

            dd = get_datadome_cookie()
            if not dd:
                print("[x] datadome failed")
                time.sleep(1); continue
            print("[✓] datadome ok")

            # Register guest
            payload_reg = json.dumps({"app_id":100067,"client_type":2,"password":password,"source":2}, separators=(',',':'))
            sig = hmac.new(API_SECRET_KEY.encode(), payload_reg.encode(), hashlib.sha256).hexdigest()
            r = requests.post("https://100067.connect.garena.com/api/v2/oauth/guest:register",
                headers={
                    "User-Agent": "GarenaMSDK/4.0.44(25028RN03A ;Android 15;ar;EG;app 1.132.1 2019121229;)",
                    "Connection": "Keep-Alive", "Accept": "application/json", "Accept-Encoding": "gzip",
                    "Authorization": f"Signature {sig}",
                    "Content-Type": "application/json; charset=utf-8",
                    "Cookie": f"datadome={dd}",
                    "Host": "100067.connect.garena.com",
                }, data=payload_reg, timeout=20, verify=False)
            print(f"[register] status={r.status_code}")
            if r.status_code != 200:
                print(f"[register] body: {r.text[:200]}")
                time.sleep(2**attempt); continue
            rj = r.json()
            if rj.get("code") != 0:
                print(f"[register] code={rj.get('code')} msg={rj.get('message','')}")
                continue
            uid = rj['data']['uid']
            print(f"[✓] uid={uid}")

            # Get token
            payload_tok = json.dumps({
                "client_id":100067, "client_secret":API_HEX_KEY, "client_type":2,
                "device_id":"02-344afb0e-593c-40b7-92f2-171972f74807",
                "password":password, "response_type":"token", "uid":uid
            }, separators=(',',':'))
            r = requests.post("https://100067.connect.garena.com/api/v2/oauth/guest/token:grant",
                headers={
                    "User-Agent": "GarenaMSDK/4.0.44(25028RN03A ;Android 15;ar;EG;app 1.132.1 2019121229;)",
                    "Connection": "Keep-Alive", "Accept": "application/json", "Accept-Encoding": "gzip",
                    "Content-Type": "application/json; charset=utf-8",
                    "Cookie": f"datadome={dd}",
                    "Host": "100067.connect.garena.com",
                }, data=payload_tok, timeout=20, verify=False)
            print(f"[token] status={r.status_code}")
            if r.status_code != 200:
                print(f"[token] body: {r.text[:200]}")
                continue
            tj = r.json()
            if tj.get("code") != 0:
                print(f"[token] code={tj.get('code')}")
                continue
            access_token = tj['data']['access_token']
            open_id = tj['data']['open_id']
            print(f"[✓] access_token ok, open_id={open_id[:8]}...")

            keystream = [0x30,0x30,0x30,0x32,0x30,0x31,0x37,0x30,0x30,0x30,0x30,0x30,0x32,0x30,0x31,0x37,0x30,0x30,0x30,0x30,0x30,0x32,0x30,0x31,0x37,0x30,0x30,0x30,0x30,0x30,0x32,0x30]
            field = codecs.decode(''.join(chr(ord(open_id[i]) ^ keystream[i % len(keystream)]) for i in range(len(open_id))).encode('unicode_escape').decode('utf-8'), 'unicode_escape').encode('latin1')

            name = f"{prefix}{random.randint(1000,9999)}"
            lang = REGION_LANG.get(region.upper(), "en")
            proto = build_proto({
                1: name, 2: access_token, 3: open_id, 5: 102000007, 6: 4, 7: 1, 13: 1, 14: field,
                15: lang, 16: 1, 17: 1, 20: "1.132.6", 21: 1,
                22: bytes.fromhex('474752450101010067020000a6a42db7bc5516876af3d1ba4adc337bac558af092eb3757d59d65c9323bba42c6593a48b74f33b2b5b3dc45cbd7ac02040db58f394045be4835213e12c35e5566445a5224f39d205fcf91c0e6bec797e7b3968ac00e90d7500b5865828a9d6f2091c3070f5319a130748e407ed57e6638974670ac045631b3d08c310cf1256cebcf1aed2d97d177534603d1c95d9c5d698340e797e72aa7ecc67a33122e48b0dfda050a1649586aca5e979be1fd9d99f48cd8cf59630e0ff60f67d4ed2ec4e5e7475970449a6c06329009ee0ce2567892587675781a31e4bb2774403b2f78e9811df2cb397fa602572266747704c6258077910902eb7420bcb4ab743d1610cddba9019e7867aaad3aa7ba9b04968064a409b66733f9f78c566a25ff478cba37a2ffe23203d4b05bceef826f174b0be7912d19432cc759325251fa094d70693fb672d6f9e799284081b3adb541dd8f27ef80dcf1e7f0ff30f2fd976659457ce41e175a2d6301b777981ccc16b9a8247abaab8de0867836c27de0146fe4d0e1fd39b86ba51f0b58601cfcbd7f6f3451fe4184b26ed44ac2f6f7bb4ce5d9a80f88c2cbfe7553e5ab97c8b028ae16b4f70f037753b8c229a6e5e9038fcbb9b4c2abb954894f8f2faf177bfdaab3b0ed537156633621d16b62d58ba4ebe518997c33e2304976ba6af9df7e7e34302c7910ae559c7e3d20a30d71c14f85c0e86f26291bbf18c2d9dfe9a908592eea4523e6c1e5d9bb5abfbebfccd5c4e136f9be777723e932b06c029df5125191000c90fde62a8e5f8fceb28648f0c69ec3037d09302b2ade908a20dbd42761ca449b2743fc362649e16235769d9fbd7f87cd64972b58d69c0441abb5d22ddc6ed059f7ac1bdbfaef8c60e64631809c5e08c7cb4074c8ce6170d94b411604986be4ae163a'),
            })
            enc_payload = bytes.fromhex(encrypt_api(proto.hex()))

            r = requests.post("https://loginbp.ppmainecoonghj.com/MajorRegister",
                headers={
                    "User-Agent": "UnityPlayer/2018.4.12f1 (UnityWebRequest/1.0, libcurl/8.5.0-DEV)",
                    "Accept-Encoding": "deflate, gzip", "X-GA-SV": "1789535859",
                    "Authorization": "Bearer", "X-GA": "v1 1", "ReleaseVersion": "OB55",
                    "Content-Type": "application/x-www-form-urlencoded", "X-Unity-Version": "2018.4.12f1",
                    "Host": "loginbp.ppmainecoonghj.com"
                }, data=enc_payload, verify=False, timeout=20)
            print(f"[major_register] status={r.status_code} len={len(r.text)}")
            if r.status_code != 200:
                print(f"[major_register] body: {r.text[:200]}")
                continue

            login = major_login(access_token, open_id, lang)
            if not login:
                print("[x] major_login failed")
                continue

            acc = {
                "account_id": login["account_id"],
                "uid": str(uid),
                "password": password,
                "name": name,
                "region": region,
                "date_created": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "jwt_token": login["jwt_token"],
                "bio_status": False
            }

            # Set bio - مباشرة بدون تأخير
            acc['bio_status'] = set_account_bio(acc['jwt_token'], BIO_TEXT)
            print(f"[✓] bio={acc['bio_status']}")

            return acc
        except Exception as e:
            print(f"[create_account] exception: {e}")
            time.sleep(0.5)
    return None


# ============ FLASK ============
app = Flask(__name__, static_folder='.')

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/generate', methods=['POST'])
def api_generate():
    data = request.json or {}
    name   = (data.get('name') or '').strip()
    server = (data.get('server') or 'ME').strip().upper()
    count  = int(data.get('count') or 1)

    if not name: return Response('{"error":"missing name"}', status=400)
    if count < 1 or count > 50: return Response('{"error":"invalid count"}', status=400)
    if server not in REGION_LANG: return Response('{"error":"invalid server"}', status=400)

    def stream():
        yield json.dumps({"type":"log","text":f"[⚡] Starting with 1 thread, target: {count} accounts","cls":"log-warn"}) + "\n"
        yield json.dumps({"type":"log","text":"[⚡] Starting generation...","cls":"log-warn"}) + "\n"

        created = 0
        bio_count = 0

        for i in range(count):
            yield json.dumps({"type":"log","text":f"\n[→] Account {i+1}/{count}...","cls":"log-info"}) + "\n"
            acc = create_account(server, name)
            if acc:
                created += 1
                if acc.get('bio_status'): bio_count += 1
                yield json.dumps({"type":"account","data":{
                    "account_id": acc['account_id'],
                    "uid": acc['uid'],
                    "password": acc['password'],
                    "name": acc['name'],
                    "region": acc['region'],
                    "date_created": acc['date_created'],
                    "bio_status": acc['bio_status']
                }}, ensure_ascii=False) + "\n"
            else:
                yield json.dumps({"type":"log","text":f"[✗] Account {i+1} failed after retries","cls":"log-error"}) + "\n"

        yield json.dumps({"type":"done","created":created,"bio":bio_count}) + "\n"

    return Response(stream(), mimetype='application/x-ndjson',
                    headers={'X-Accel-Buffering':'no','Cache-Control':'no-cache'})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print("="*50)
    print("  Free Fire Guest Generator")
    print("="*50)
    print(f"[✓] http://localhost:{port}")
    print("[!] Ctrl+C to stop\n")
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
