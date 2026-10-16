from pathlib import Path
import traceback

from config import load_config
from dispatcher import Dispatcher
from graph import build_graph, opening_messages
from model_runtime import ModelRuntime
from provider import model
from runner import _alerts
from scan import Scan
from trace import Trace
from workspace import AgentWorkspace

config = load_config(Path("runs/configs/owasp-full.toml"), Path("targets/BenchmarkPython"))
alert = _alerts(Scan(config.fixture).discover(config.scan))[0]
with Trace("debug", Path("runs/debug-trace.jsonl")) as trace:
    try:
        runtime = ModelRuntime(model(config), trace, config)
        with AgentWorkspace(config, is_owasp=True, case=Path(alert["filename"]).stem) as workspace:
            dispatcher = Dispatcher(workspace, trace, alert["alert_id"])
            state = build_graph(trace, runtime, dispatcher).invoke({
                "alert_id": alert["alert_id"],
                "alert": alert,
                "messages": opening_messages(alert),
            })
            print(state)
        trace.terminal(state["status"] if state.get("status") != "classified" else "complete")
    except Exception:
        traceback.print_exc()
        trace.terminal("error")
        raise
