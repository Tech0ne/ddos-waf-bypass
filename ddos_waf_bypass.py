import base64
import re

from bs4 import BeautifulSoup
from requests import Session


def get_sequence(data: str):
    functions = {
        "escape": escape,
        "window.atob": b64decode,
        "decodeURIComponent": decodeURIComponent,
    }
    final = []
    for fct in data.split(")")[0].split("(")[::-1]:
        if "eval" in fct or "+" in fct or not fct:
            continue
        if fct not in functions.keys():
            print(f"=== Unkown: {fct} ===")
            continue
        final.append(functions[fct])
    return final


def splits(to_split: str, subs: str):
    final = [to_split]
    for char in subs:
        final = [item for substring in final for item in substring.split(char)]
    while "" in final:
        final.remove("")
    return final


def evaluate_string(string: str, variables: dict) -> str:
    return "".join([variables[name] for name in splits(string, " \t\n+")])


def escape(data: bytes) -> bytes:
    hex_encode_chars = (
        b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789@*_+-./"
    )

    result = b""
    for byte in data:
        if byte in hex_encode_chars:
            result += bytes([byte])
        else:
            result += b"%" + hex(byte)[2:].upper().zfill(2).encode("ascii")

    return result


def b64decode(data: bytes) -> bytes:
    while len(data) % 4:
        data += b"="
    return base64.b64decode(data)


def decodeURIComponent(encoded_bytes):
    pattern = re.compile(b"%([0-9A-Fa-f]{2})|%u([0-9A-Fa-f]{4})")

    def decode_match(match):
        hex_value = match.group(1) or match.group(2)
        if len(hex_value) == 2:
            return bytes([int(hex_value, 16)])
        elif len(hex_value) == 4:
            unicode_char = int(hex_value, 16)
            return chr(unicode_char).encode("utf-8")

    decoded_bytes = pattern.sub(decode_match, encoded_bytes)

    return decoded_bytes


def get_var_value(data: str) -> str:
    value = 0
    splited = data.split("parseInt(")
    for i in range(len(splited)):
        if not i:
            continue
        element = splited[i]
        value += int(
            element.split(", ")[0][1:-1], int(element.split(")")
                                              [0].split(" ")[-1])
        )
    return value


def dcode(data: str):
    variables = {}
    final = None
    for action in data.split(";"):
        while (
            action.startswith(" ") or action.startswith(
                "\t") or action.startswith("\n")
        ):
            action = action[1:]
        if not action:
            continue
        if action.startswith("var"):
            variables[action.split("=")[0].split(" ")[-1].split("\t")[-1]] = (
                action.split("'")[1]
                if action.count("'") > action.count('"')
                else action.split('"')[1]
            )
        elif action.startswith("eval"):
            final = action.split(")")[0].split("(")[-1]
            if not (final.startswith("'") or final.startswith('"')):
                final = evaluate_string(final, variables)
    final = final.encode()
    element = "'" if data.count("'") > data.count('"') else '"'
    for i in range(len(data.split(element))):
        if not i % 2:
            continue
        final += data.split(element)[i].encode()
    if b"\\x" in final:
        final = final.decode("unicode_escape").encode()
    seq = []
    if data.startswith("eval"):
        seq.extend(get_sequence(data.split(element)[0]))
    else:
        seq.extend(get_sequence(data.split(element)[-1]))
    for fct in seq:
        final = fct(final)
    final = final.split(b")();")[0] + b")();"
    return final


def login(token: str) -> Session:
    global logs
    s = Session()
    s.headers.update(
        {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/115.0"
        }
    )

    init = s.get("https://intra.epitech.eu/")
    soup = BeautifulSoup(init.text, "html.parser")

    scripts = soup.find_all("script", {"charset": "utf-8"})

    data = scripts[0].contents[0]

    output = dcode(data).decode()

    cookie = output.split("document.cookie = ")[1].split(" ")[0][1:-1]

    s.cookies.set(*cookie.split("="))

    var_name = output.split("/*HttpOnly Cookie flags prevent this*/\n    var ")[
        1
    ].split("=")[0]
    var_value = output.split(f"var {var_name}=")[1].split("\n")[0]

    var_value = get_var_value(var_value)

    header = output.split("xhttp.setRequestHeader('")[1].split("'")[0]

    headers = {
        header: str(var_value),
        "X-Requested-with": "XMLHttpRequest",
        "X-Requested-TimeStamp": "",
        "X-Requested-TimeStamp-Expire": "",
        "X-Requested-TimeStamp-Combination": "",
        "X-Requested-Type": "GET",
        "X-Requested-Type-Combination": "GET",
    }

    s.post(
        "https://intra.epitech.eu",
        data=output.split("xhttp.send(")[1].split(")")[0][1:-1],
        headers=headers,
    )

    s.get("https://intra.epitech.eu")

    s.cookies.set("user", token)

    return s
