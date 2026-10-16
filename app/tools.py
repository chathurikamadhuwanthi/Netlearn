from flask import (Blueprint, abort, jsonify, redirect, render_template,
                   request, session, url_for)
from .services import labs, routing_sim, subnet_tools

bp = Blueprint("tools", __name__, url_prefix="/tools")


@bp.route("/subnet", methods=("GET", "POST"))
def subnet():
    address = request.form.get("address", "")
    new_prefix = request.form.get("new_prefix", "")
    result, error = None, None

    if request.method == "POST":
        try:
            result = subnet_tools.analyze(address, new_prefix)
        except ValueError as e:
            error = str(e)

    return render_template("tools/subnet.html", result=result, error=error,
                           address=address, new_prefix=new_prefix)


@bp.route("/packet-walk")
def packet_walk():
    start = request.args.get("start", "R1")
    dest = request.args.get("dest", "").strip()
    result, error = None, None

    if dest:
        try:
            result = routing_sim.walk(start, dest)
        except ValueError as e:
            error = str(e)

    return render_template("tools/packet_walk.html", result=result, error=error,
                           start=start, dest=dest,
                           routers=routing_sim.router_choices(),
                           tables=routing_sim.all_tables(),
                           examples=routing_sim.EXAMPLES)


# ---------- Net Labs (Lab 1, 2 and 3) ----------

def _get_lab(lab_id):
    meta = labs.LABS.get(lab_id)
    if meta is None:
        abort(404)
    return meta


def _lab_state(meta):
    # Each lab keeps its own configuration in the user's session
    key = f"lab{meta['n']}"
    st = session.get(key)
    if not st or "modes" not in st:
        st = meta["sim"].new_state()
        session[key] = st
    return st


def _prompts(meta, st):
    return {d: meta["sim"].prompt(st, d) for d in meta["sim"].ROUTER_NAMES}


@bp.route("/cli-lab")
def cli_lab():
    # Old address: now opens Lab 1
    return redirect(url_for("tools.lab", lab_id=1))


@bp.route("/labs/<int:lab_id>")
def lab(lab_id):
    meta = _get_lab(lab_id)
    st = _lab_state(meta)
    return render_template("tools/lab.html", lab=meta,
                           devices=meta["sim"].ROUTER_NAMES, prompts=_prompts(meta, st))


@bp.route("/labs/<int:lab_id>/cmd", methods=("POST",))
def lab_cmd(lab_id):
    meta = _get_lab(lab_id)
    data = request.get_json(silent=True) or {}
    device = data.get("router")
    line = str(data.get("cmd", ""))[:200]
    if device not in meta["sim"].ROUTER_NAMES:
        return jsonify(output="% Unknown device", prompt=""), 400

    st = _lab_state(meta)
    output = meta["sim"].execute(st, device, line)
    session[f"lab{meta['n']}"] = st
    session.modified = True
    return jsonify(output=output, prompt=meta["sim"].prompt(st, device))


@bp.route("/labs/<int:lab_id>/check", methods=("POST",))
def lab_check(lab_id):
    meta = _get_lab(lab_id)
    return jsonify(meta["sim"].check(_lab_state(meta)))


@bp.route("/labs/<int:lab_id>/reset", methods=("POST",))
def lab_reset(lab_id):
    meta = _get_lab(lab_id)
    st = meta["sim"].new_state()
    session[f"lab{meta['n']}"] = st
    session.modified = True
    return jsonify(prompts=_prompts(meta, st))