"""Builds a tiny fake Unreal project with deliberate problems and checks scripts/project_scan.py flags them."""
import importlib.util
import pathlib
import subprocess
import tempfile


def w(root, rel, text):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def run(skill, check):
    spec = importlib.util.spec_from_file_location("unreal_scan", skill / "scripts/project_scan.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    with tempfile.TemporaryDirectory() as d:
        r = pathlib.Path(d)
        w(r, "MyGame.uproject", '{"EngineAssociation":"5.4","Modules":[{"Name":"MyGame"}],"Plugins":[{"Name":"EnhancedInput","Enabled":true}]}')
        w(r, "Config/DefaultEngine.ini", "[/Script/EngineSettings.GameMapsSettings]\nGameDefaultMap=/Game/Maps/Missing.Missing\n")
        w(r, "Config/DefaultGame.ini", "[/Script/UnrealEd.ProjectPackagingSettings]\nbCookAll=True\nIncludeDebugFiles=True\n")
        w(r, ".gitignore", "Binaries/\n")
        w(r, ".gitattributes", "*.png filter=lfs diff=lfs merge=lfs -text\n")
        w(r, "Content/StarterContent/Props/SM_Chair.uasset", "x")
        w(r, "Content/Hero Mesh.uasset", "x")
        w(r, "Content/Chair.uasset", "x")
        w(r, "Source/MyGame/MyGame.Build.cs", "public class MyGame : ModuleRules {}")
        w(r, "Source/MyGame/MyActor.h", '#pragma once\n#include "Engine.h"\nUCLASS()\nclass AMyActor : public AActor {\n  GENERATED_BODY()\n  UStaticMeshComponent* Mesh;\n  UPROPERTY()\n  AActor* Target;\n};\n')
        w(r, "Source/MyGame/MyActor.cpp", 'AMyActor::AMyActor() { PrimaryActorTick.bCanEverTick = true; static ConstructorHelpers::FObjectFinder<UStaticMesh> M(TEXT("/Game/Meshes/SM_Box")); }\n'
             'void AMyActor::Tick(float D) { TArray<AActor*> A; UGameplayStatics::GetAllActorsOfClass(GetWorld(), AActor::StaticClass(), A); GEngine->AddOnScreenDebugMessage(-1, 1, FColor::Red, TEXT("x")); }\n')
        g = lambda *a: subprocess.run(["git", "-C", d, *a], capture_output=True, text=True)
        g("init", "-q"); g("config", "user.email", "t@t"); g("config", "user.name", "t")
        w(r, "Saved/Logs/x.log", "x")
        g("add", "-A"); g("commit", "-qm", "init")
        res = mod.scan(d, 25)
    rules = {x["rule"] for x in res["results"]}
    for rid in ["DEFAULT_MAP_MISSING", "COOK_ALL", "PACKAGE_DEBUG_FILES", "GITIGNORE_GAP", "NO_LFS_FOR_UASSETS", "GENERATED_FOLDER_COMMITTED",
                "STARTER_CONTENT", "NAME_SPACES_OR_SYMBOLS", "ASSET_WITHOUT_TYPE_PREFIX", "HEAVY_INCLUDE_IN_HEADER", "RAW_UOBJECT_POINTER",
                "EXPENSIVE_IN_TICK", "HARDCODED_ASSET_PATH", "CONSTRUCTOR_HARD_REFERENCE", "DEBUG_MESSAGE_IN_SHIPPING", "NO_AUTOMATION_TESTS"]:
        check(rid in rules, f"unreal: {rid} detected")
    raw = next(x for x in res["results"] if x["rule"] == "RAW_UOBJECT_POINTER")
    check(raw["count"] == 1, "unreal: UPROPERTY-marked pointer not flagged")
    check(res["facts"].get("engine") == "5.4", "unreal: engine version read")
