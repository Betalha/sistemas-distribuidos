"""SOAP 1.2 escrito à mão (um POST /soap, operação = nome do 1º filho do Body). uvicorn soap_server:app
ponytail: sem WSDL (o contrato fica em soap_wsdl.xml só como documentação); bibliotecas SOAP Python (spyne/zeep-server) estão abandonadas."""
import xml.etree.ElementTree as ET
from fastapi import FastAPI, Request, Response
import data

NS = "http://www.w3.org/2003/05/soap-envelope"
ENV = f'<?xml version="1.0"?><soap:Envelope xmlns:soap="{NS}"><soap:Body>%s</soap:Body></soap:Envelope>'
app = FastAPI()


def to_xml(tag, v):
    if isinstance(v, dict):
        return f"<{tag}>" + "".join(to_xml(k, x) for k, x in v.items()) + f"</{tag}>"
    if isinstance(v, list):
        return f"<{tag}>" + "".join(to_xml("item" if not tag.endswith("_ids") else "song_id", x) for x in v) + f"</{tag}>"
    return f"<{tag}>{v}</{tag}>"


def cast(p):
    for k in ("id", "user_id", "playlist_id", "song_id"):
        if k in p: p[k] = int(p[k])
    if "song_ids" in p: p["song_ids"] = [int(x) for x in p["song_ids"].split(",") if x]
    return p


OPS = {}
for kind, name in (("users", "User"), ("songs", "Song"), ("playlists", "Playlist")):
    OPS[f"List{name}s"] = lambda p, k=kind: data.list_(k)
    OPS[f"Get{name}"] = lambda p, k=kind: data.get(k, p["id"])
    OPS[f"Create{name}"] = lambda p, k=kind: data.create(k, p)
    OPS[f"Update{name}"] = lambda p, k=kind: data.update(k, p["id"], p)
    OPS[f"Delete{name}"] = lambda p, k=kind: {"deleted": data.delete(k, p["id"])}
OPS["ListPlaylistsByUser"] = lambda p: data.playlists_of_user(p["user_id"])
OPS["ListSongsByPlaylist"] = lambda p: data.songs_of_playlist(p["playlist_id"])
OPS["ListPlaylistsBySong"] = lambda p: data.playlists_with_song(p["song_id"])


def fault(msg):
    return Response(ENV % f"<soap:Fault><soap:Reason><soap:Text>{msg}</soap:Text></soap:Reason></soap:Fault>",
                    500, media_type="application/soap+xml")


@app.post("/soap")
async def soap(req: Request):
    try:
        op = ET.fromstring(await req.body()).find(f"{{{NS}}}Body")[0]
        name = op.tag.split("}")[-1]
        r = OPS[name](cast({c.tag.split("}")[-1]: c.text or "" for c in op}))
        if r is None: return fault("not found")
        return Response(ENV % to_xml(name + "Response", r), media_type="application/soap+xml")
    except Exception as e:
        return fault(type(e).__name__)
