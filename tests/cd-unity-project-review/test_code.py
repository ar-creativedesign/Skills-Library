"""Builds a tiny fake Unity project with deliberate problems and checks scripts/project_scan.py flags them."""
import importlib.util
import pathlib
import subprocess
import tempfile


def w(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def run(skill, check):
    spec = importlib.util.spec_from_file_location("unity_scan", skill / "scripts/project_scan.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    with tempfile.TemporaryDirectory() as d:
        r = pathlib.Path(d)
        w(r, "ProjectSettings/ProjectVersion.txt", "m_EditorVersion: 2023.2.5f1\n")
        w(r, "ProjectSettings/ProjectSettings.asset", "  m_ActiveColorSpace: 0\n  activeInputHandler: 2\n  gcIncremental: 0\n")
        w(r, "ProjectSettings/EditorSettings.asset", "  m_SerializationMode: 0\n  m_ExternalVersionControlSupport: Hidden Meta Files\n")
        w(r, "ProjectSettings/EditorBuildSettings.asset", "  m_Scenes:\n  - enabled: 1\n    path: Assets/Scenes/Gone.unity\n")
        w(r, "Packages/manifest.json", '{"dependencies":{"com.unity.inputsystem":"1.7.0","com.foo.bar":"https://github.com/foo/bar.git","com.unity.x":"2.0.0-pre.3"}}')
        w(r, ".gitignore", "/Temp/\n")
        w(r, "Assets/Scripts/Player.cs", "using UnityEngine;\nusing UnityEditor;\npublic class Player : MonoBehaviour {\n"
             " public int a;\n public int b;\n public int c;\n public float d;\n public string e;\n"
             " void Update() { var rb = GetComponent<Rigidbody>(); var e = FindObjectOfType<Camera>(); }\n"
             " void Start() { }\n async void Load() { }\n void Go() { Invoke(\"Go\", 1f); }\n}\n")
        w(r, "Assets/Scripts/Player.cs.meta", "guid: 1\n")
        w(r, "Assets/Scripts.meta", "guid: 2\n")
        w(r, "Assets/Orphan.png.meta", "guid: 3\n")
        w(r, "Assets/My Texture.png", "x")
        w(r, "Assets/My Texture.png.meta", "TextureImporter:\n  isReadable: 1\n  textureType: 8\n  enableMipMap: 1\n  maxTextureSize: 8192\n")
        w(r, "Assets/Resources/Data.asset", "x")
        w(r, "Assets/Resources.meta", "guid: 4\n")
        g = lambda *a: subprocess.run(["git", "-C", d, *a], capture_output=True, text=True)
        g("init", "-q"); g("config", "user.email", "t@t"); g("config", "user.name", "t")
        w(r, "Library/ArtifactDB", "x")
        g("add", "-A"); g("commit", "-qm", "init")
        res = mod.scan(d, 25)
    rules = {x["rule"] for x in res["results"]}
    for rid in ["NON_LTS_EDITOR", "PREVIEW_PACKAGE", "UNPINNED_GIT_PACKAGE", "GAMMA_COLOR_SPACE", "BOTH_INPUT_SYSTEMS", "INCREMENTAL_GC_OFF",
                "NOT_FORCE_TEXT", "HIDDEN_META_FILES", "GITIGNORE_GAP", "NO_LFS", "GENERATED_FOLDER_COMMITTED", "MISSING_META", "ORPHAN_META",
                "NAME_SPACES_OR_SYMBOLS", "RESOURCES_FOLDER", "BUILD_SCENE_MISSING", "TEXTURE_READ_WRITE", "SPRITE_MIPMAPS", "TEXTURE_8K",
                "EDITOR_API_IN_RUNTIME", "NO_NAMESPACE", "EXPENSIVE_IN_FRAME_LOOP", "EMPTY_UNITY_CALLBACK", "ASYNC_VOID", "STRING_BASED_CALL",
                "MANY_PUBLIC_FIELDS", "NO_TESTS"]:
        check(rid in rules, f"unity: {rid} detected")
    check(res["facts"].get("render_pipeline") == "Built-in", "unity: render pipeline detected")
