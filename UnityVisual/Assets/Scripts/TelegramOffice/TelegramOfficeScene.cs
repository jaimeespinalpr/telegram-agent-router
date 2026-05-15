using System.Collections.Generic;
using UnityEngine;

namespace TelegramOffice
{
    [ExecuteAlways]
    public sealed class TelegramOfficeScene : MonoBehaviour
    {
        private const string GeneratedRootName = "Generated Lobby Preview";

        private readonly Dictionary<string, AgentCharacter> characters = new();
        private readonly Dictionary<string, Transform> roomCenters = new();
        private readonly Dictionary<string, Color> accents = new();
        private readonly Dictionary<string, Vector3> routeTargets = new();
        private MessagePacket packet;
        private string currentRoute = "";
        private Transform sceneRoot;

        private void Awake()
        {
            EnsureScene();

            if (Application.isPlaying)
            {
                EnsureApiClient();
            }
        }

        private void OnEnable()
        {
            if (!Application.isPlaying)
            {
                EnsureScene();
            }
        }

        [ContextMenu("Rebuild Lobby Preview")]
        public void EnsureScene()
        {
            characters.Clear();
            roomCenters.Clear();
            accents.Clear();
            routeTargets.Clear();
            currentRoute = "";

            ClearGeneratedRoot();
            sceneRoot = new GameObject(GeneratedRootName).transform;
            sceneRoot.SetParent(transform, false);

            BuildCamera();
            BuildScene();
        }

        private void EnsureApiClient()
        {
            var api = GetComponent<RouterApiClient>();
            if (api == null)
            {
                api = gameObject.AddComponent<RouterApiClient>();
            }
            api.SceneStateReceived -= OnSceneStateReceived;
            api.SceneStateReceived += OnSceneStateReceived;
        }

        private void ClearGeneratedRoot()
        {
            var existing = transform.Find(GeneratedRootName);
            if (existing == null)
            {
                return;
            }

            if (Application.isPlaying)
            {
                Destroy(existing.gameObject);
            }
            else
            {
                DestroyImmediate(existing.gameObject);
            }
        }

        private void BuildCamera()
        {
            var cameraObject = GameObject.Find("Main Camera");
            if (cameraObject == null)
            {
                cameraObject = new GameObject("Main Camera");
            }

            var camera = cameraObject.GetComponent<Camera>();
            if (camera == null)
            {
                camera = cameraObject.AddComponent<Camera>();
            }
            camera.orthographic = true;
            camera.orthographicSize = 6.35f;
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = new Color(0.02f, 0.025f, 0.07f);
            cameraObject.transform.position = new Vector3(0, 0, -10);
            cameraObject.tag = "MainCamera";
        }

        private void BuildScene()
        {
            BuildLightingRig();
            BuildFloor();
            BuildRoom("router", new Vector2(-4.8f, 2.45f), new Color(0.23f, 0.37f, 0.2f), new Color(0.47f, 0.94f, 0.61f));
            BuildRoom("multi", new Vector2(4.8f, 2.45f), new Color(0.15f, 0.24f, 0.44f), new Color(0.41f, 0.66f, 1f));
            BuildRoom("ardida", new Vector2(-4.8f, -2.45f), new Color(0.4f, 0.2f, 0.37f), new Color(1f, 0.45f, 0.83f));
            BuildRoom("prpagyda", new Vector2(4.8f, -2.45f), new Color(0.14f, 0.37f, 0.36f), new Color(0.32f, 0.9f, 0.95f));
            BuildRoom("prjimenezda", new Vector2(0f, -3.25f), new Color(0.46f, 0.34f, 0.16f), new Color(1f, 0.82f, 0.35f));

            packet = new GameObject("Message Packet").AddComponent<MessagePacket>();
            packet.transform.SetParent(sceneRoot, false);
            packet.Build();
        }

        private void BuildLightingRig()
        {
            BuildBackdrop();
        }

        private void BuildBackdrop()
        {
            PixelPart.Rect("deep-space-backdrop", sceneRoot, new Vector2(0, 0), new Vector2(16f, 10f), new Color(0.015f, 0.018f, 0.055f), -20);
            PixelPart.Rect("blue-vignette", sceneRoot, new Vector2(0, 0.7f), new Vector2(13f, 7f), new Color(0.05f, 0.07f, 0.16f, 0.45f), -19);
            for (var i = 0; i < 42; i++)
            {
                var x = Mathf.Repeat(i * 1.73f, 13.5f) - 6.75f;
                var y = Mathf.Repeat(i * 2.19f, 7.2f) - 3.2f;
                var size = i % 5 == 0 ? 0.05f : 0.025f;
                PixelPart.Rect($"star-{i}", sceneRoot, new Vector2(x, y), new Vector2(size, size), new Color(0.75f, 0.85f, 1f, 0.45f), -18);
            }
        }

        private void BuildFloor()
        {
            var floor = new GameObject("Isometric Tilemap Lobby");
            floor.transform.SetParent(sceneRoot, false);

            for (var x = -7; x <= 7; x++)
            {
                for (var y = -5; y <= 5; y++)
                {
                    if (Mathf.Abs(x) + Mathf.Abs(y) > 9)
                    {
                        continue;
                    }

                    var position = IsoToWorld(x, y);
                    var shade = ((x + y) & 1) == 0 ? Color.white : new Color(0.82f, 0.9f, 1f);
                    if (KenneySpriteLibrary.Has("floor_N"))
                    {
                        KenneySpriteLibrary.Place($"kenney-floor-{x}-{y}", floor.transform, "floor_N", position, 0.42f, x + y, shade);
                    }
                    else
                    {
                        PixelPart.Diamond(
                            $"iso-tile-{x}-{y}",
                            floor.transform,
                            position,
                            new Vector2(1.05f, 1.05f),
                            new Color(0.64f, 0.36f, 0.19f) * (shade.r),
                            new Color(0.22f, 0.14f, 0.13f),
                            0
                        );
                    }
                }
            }

            if (KenneySpriteLibrary.Has("floor_N"))
            {
                BuildLobbyShell();
            }

            PixelPart.Diamond("lobby-rug-outer", sceneRoot, Vector2.zero, new Vector2(2.9f, 1.7f), new Color(0.22f, 0.41f, 0.45f), new Color(0.14f, 0.24f, 0.28f), 2);
            PixelPart.Diamond("lobby-rug-inner", sceneRoot, new Vector2(0, 0.05f), new Vector2(2.0f, 1.15f), new Color(0.88f, 0.56f, 0.2f), new Color(0.3f, 0.18f, 0.12f), 3);
            PixelPart.Rect("center-planter", sceneRoot, new Vector2(0, 0.16f), new Vector2(0.72f, 0.42f), new Color(0.56f, 0.3f, 0.18f), 8);
            PixelPart.Rect("center-leaf-l", sceneRoot, new Vector2(-0.28f, 0.62f), new Vector2(0.34f, 0.72f), new Color(0.27f, 0.8f, 0.38f), 9);
            PixelPart.Rect("center-leaf-r", sceneRoot, new Vector2(0.28f, 0.62f), new Vector2(0.34f, 0.72f), new Color(0.38f, 0.93f, 0.49f), 9);
            PixelPart.Rect("center-leaf-top", sceneRoot, new Vector2(0, 0.82f), new Vector2(0.3f, 0.86f), new Color(0.21f, 0.74f, 0.35f), 10);
            BuildSofa("left-sofa", new Vector2(-1.85f, -1.2f), false);
            BuildSofa("right-sofa", new Vector2(1.85f, -1.2f), true);
            BuildWayfinder("A", new Vector2(-2.9f, 1.15f), new Color(0.47f, 0.94f, 0.61f));
            BuildWayfinder("B", new Vector2(2.9f, 1.15f), new Color(0.41f, 0.66f, 1f));
            BuildWayfinder("C", new Vector2(-2.75f, -1.55f), new Color(1f, 0.45f, 0.83f));
            BuildWayfinder("D", new Vector2(2.75f, -1.55f), new Color(0.32f, 0.9f, 0.95f));
            BuildWayfinder("E", new Vector2(0, -2.25f), new Color(1f, 0.82f, 0.35f));
        }

        private void BuildLobbyShell()
        {
            var shell = new GameObject("Kenney Lobby Shell");
            shell.transform.SetParent(sceneRoot, false);

            for (var x = -6; x <= 6; x++)
            {
                KenneySpriteLibrary.Place($"north-wall-{x}", shell.transform, "wall_N", IsoToWorld(x, 5), 0.42f, 18 + x);
                KenneySpriteLibrary.Place($"south-rail-{x}", shell.transform, x % 3 == 0 ? "fence_N" : "slab_N", IsoToWorld(x, -5), 0.42f, 7 + x);
            }

            for (var y = -4; y <= 4; y++)
            {
                KenneySpriteLibrary.Place($"west-wall-{y}", shell.transform, "wall_W", IsoToWorld(-7, y), 0.42f, 12 + y);
                KenneySpriteLibrary.Place($"east-wall-{y}", shell.transform, "wall_E", IsoToWorld(7, y), 0.42f, 12 + y);
            }

            KenneySpriteLibrary.Place("north-door", shell.transform, "doorOpen_N", IsoToWorld(0, 5), 0.42f, 28);
            KenneySpriteLibrary.Place("left-window", shell.transform, "windowMiddle_W", IsoToWorld(-7, 2), 0.42f, 24);
            KenneySpriteLibrary.Place("right-window", shell.transform, "windowMiddle_E", IsoToWorld(7, 2), 0.42f, 24);
            KenneySpriteLibrary.Place("lobby-column-left", shell.transform, "column_N", IsoToWorld(-4, -2), 0.42f, 20);
            KenneySpriteLibrary.Place("lobby-column-right", shell.transform, "column_N", IsoToWorld(4, -2), 0.42f, 20);
            KenneySpriteLibrary.Place("center-crate-a", shell.transform, "crate_N", new Vector2(-0.65f, -0.95f), 0.26f, 14);
            KenneySpriteLibrary.Place("center-crate-b", shell.transform, "crate_E", new Vector2(0.72f, -0.9f), 0.26f, 14);
        }

        private void BuildRoom(string id, Vector2 center, Color wall, Color accent)
        {
            accents[id] = accent;
            var room = new GameObject($"Room {id}");
            room.transform.SetParent(sceneRoot, false);
            room.transform.localPosition = center;
            roomCenters[id] = room.transform;
            routeTargets[id] = center;

            if (KenneySpriteLibrary.Has("floor_N"))
            {
                BuildKenneyRoomShell(id, room.transform, accent);
            }
            else
            {
                PixelPart.Diamond("room-platform-shadow", room.transform, new Vector2(0.06f, -0.9f), new Vector2(3.6f, 1.58f), new Color(0, 0, 0, 0.25f), new Color(0, 0, 0, 0.3f), 4);
                PixelPart.Rect("back-frame", room.transform, new Vector2(0, 0.15f), new Vector2(3.75f, 2.15f), new Color(0.29f, 0.2f, 0.25f), 5);
                PixelPart.Rect("wall", room.transform, new Vector2(0, 0.24f), new Vector2(3.42f, 1.9f), wall, 6);
                PixelPart.Rect("wall-shade", room.transform, new Vector2(0, -0.36f), new Vector2(3.42f, 0.22f), wall * 0.7f, 7);
                PixelPart.Diamond("iso-room-floor", room.transform, new Vector2(0, -0.78f), new Vector2(3.2f, 1.25f), new Color(0.52f, 0.29f, 0.17f), new Color(0.21f, 0.13f, 0.12f), 8);
                PixelPart.Rect("door-left", room.transform, new Vector2(-1.46f, -0.58f), new Vector2(0.34f, 0.88f), new Color(0.43f, 0.23f, 0.14f), 9);
                PixelPart.Rect("door-right", room.transform, new Vector2(1.46f, -0.58f), new Vector2(0.34f, 0.88f), new Color(0.43f, 0.23f, 0.14f), 9);
            }

            PixelPart.Rect("neon", room.transform, new Vector2(1.1f, 0.72f), new Vector2(0.62f, 0.38f), accent, 10);
            PixelPart.Rect("neon-core", room.transform, new Vector2(1.1f, 0.72f), new Vector2(0.38f, 0.16f), Color.white, 11);
            BuildRoomLight(room.transform, new Vector2(1.1f, 0.72f), accent);
            PixelPart.Rect("desk", room.transform, new Vector2(0.15f, -0.8f), new Vector2(1.7f, 0.44f), new Color(0.55f, 0.31f, 0.18f), 18);
            PixelPart.Rect("desk-top", room.transform, new Vector2(0.15f, -0.58f), new Vector2(1.82f, 0.14f), new Color(0.72f, 0.43f, 0.22f), 19);
            PixelPart.Rect("monitor", room.transform, new Vector2(0.55f, -0.28f), new Vector2(0.62f, 0.42f), new Color(0.04f, 0.06f, 0.1f), 22);
            PixelPart.Rect("monitor-glow", room.transform, new Vector2(0.55f, -0.28f), new Vector2(0.42f, 0.2f), accent, 23);
            PixelPart.Rect("side-monitor", room.transform, new Vector2(1.05f, -0.34f), new Vector2(0.46f, 0.34f), new Color(0.04f, 0.06f, 0.1f), 22);
            PixelPart.Rect("side-monitor-glow", room.transform, new Vector2(1.05f, -0.34f), new Vector2(0.28f, 0.16f), accent * 0.85f, 23);
            BuildRoomProps(id, room.transform, accent);

            var character = new GameObject($"Character {id}").AddComponent<AgentCharacter>();
            character.transform.SetParent(room.transform, false);
            character.transform.localPosition = new Vector3(-0.52f, -0.28f, 0);
            character.Build(
                id,
                id == "prjimenezda" ? new Color(0.72f, 0.46f, 0.31f) : new Color(0.94f, 0.69f, 0.48f),
                id switch
                {
                    "router" => new Color(0.42f, 0.2f, 0.11f),
                    "multi" => new Color(0.08f, 0.53f, 1f),
                    "ardida" => new Color(1f, 0.37f, 0.86f),
                    "prpagyda" => new Color(0.08f, 0.72f, 0.66f),
                    _ => new Color(0.12f, 0.08f, 0.09f)
                },
                id switch
                {
                    "router" => new Color(0.05f, 0.25f, 0.62f),
                    "multi" => new Color(0.16f, 0.43f, 0.95f),
                    "ardida" => new Color(0.95f, 0.28f, 0.75f),
                    "prpagyda" => new Color(0.1f, 0.72f, 0.58f),
                    _ => new Color(1f, 0.74f, 0.17f)
                },
                accent
            );
            characters[id] = character;
        }

        private void BuildRoomLight(Transform parent, Vector2 localPosition, Color accent)
        {
            PixelPart.Rect("room-accent-glow-wide", parent, localPosition, new Vector2(1.7f, 1.15f), new Color(accent.r, accent.g, accent.b, 0.16f), 9);
            PixelPart.Rect("room-accent-glow-core", parent, localPosition, new Vector2(0.84f, 0.58f), new Color(accent.r, accent.g, accent.b, 0.24f), 10);
        }

        private void BuildKenneyRoomShell(string id, Transform parent, Color accent)
        {
            PixelPart.Diamond("room-platform-shadow", parent, new Vector2(0.08f, -1.02f), new Vector2(3.9f, 1.65f), new Color(0, 0, 0, 0.28f), new Color(0, 0, 0, 0.18f), 4);

            var roomTint = id switch
            {
                "router" => new Color(0.82f, 1f, 0.82f),
                "multi" => new Color(0.78f, 0.87f, 1f),
                "ardida" => new Color(1f, 0.78f, 0.96f),
                "prpagyda" => new Color(0.76f, 1f, 0.96f),
                _ => new Color(1f, 0.92f, 0.7f)
            };

            KenneySpriteLibrary.Place("floor-left", parent, "floor_N", new Vector2(-0.5f, -0.88f), 0.38f, 8, roomTint);
            KenneySpriteLibrary.Place("floor-right", parent, "floor_N", new Vector2(0.5f, -0.88f), 0.38f, 8, roomTint);
            KenneySpriteLibrary.Place("floor-back-left", parent, "floor_N", new Vector2(-0.5f, -0.42f), 0.38f, 9, roomTint * 0.95f);
            KenneySpriteLibrary.Place("floor-back-right", parent, "floor_N", new Vector2(0.5f, -0.42f), 0.38f, 9, roomTint * 0.95f);

            KenneySpriteLibrary.Place("back-wall-left", parent, "wall_N", new Vector2(-0.48f, 0.02f), 0.38f, 10, roomTint * 0.82f);
            KenneySpriteLibrary.Place("back-wall-right", parent, "wall_N", new Vector2(0.48f, 0.02f), 0.38f, 10, roomTint * 0.82f);
            KenneySpriteLibrary.Place("left-wall", parent, "wall_W", new Vector2(-1.32f, -0.34f), 0.38f, 11, roomTint * 0.72f);
            KenneySpriteLibrary.Place("right-wall", parent, "wall_E", new Vector2(1.32f, -0.34f), 0.38f, 11, roomTint * 0.76f);
            KenneySpriteLibrary.Place("window-left", parent, "windowMiddle_W", new Vector2(-1.31f, 0.36f), 0.38f, 15);
            KenneySpriteLibrary.Place("window-right", parent, "windowMiddle_E", new Vector2(1.31f, 0.36f), 0.38f, 15);
            KenneySpriteLibrary.Place("door", parent, "doorOpen_S", new Vector2(0f, -1.12f), 0.36f, 18);
            KenneySpriteLibrary.Place("corner-column-l", parent, "column_N", new Vector2(-1.62f, -0.88f), 0.28f, 18);
            KenneySpriteLibrary.Place("corner-column-r", parent, "column_N", new Vector2(1.62f, -0.88f), 0.28f, 18);

            var signAsset = id switch
            {
                "router" => "switchWallOn_N",
                "multi" => "arrowWall_N",
                "ardida" => "switchWallOff_N",
                "prpagyda" => "window_N",
                _ => "arrow_N"
            };
            KenneySpriteLibrary.Place("role-prop", parent, signAsset, new Vector2(0f, 0.72f), 0.22f, 19, accent);
            KenneySpriteLibrary.Place("storage-crate", parent, "crate_N", new Vector2(-1.08f, -0.82f), 0.2f, 20);
        }

        private void BuildWayfinder(string label, Vector2 position, Color accent)
        {
            var sign = new GameObject($"Wayfinder {label}");
            sign.transform.SetParent(sceneRoot, false);
            sign.transform.localPosition = position;
            PixelPart.Rect("sign-shadow", sign.transform, new Vector2(0.04f, -0.04f), new Vector2(0.42f, 0.42f), new Color(0, 0, 0, 0.22f), 20);
            PixelPart.Rect("sign-body", sign.transform, Vector2.zero, new Vector2(0.36f, 0.36f), accent, 21);
            PixelPart.Rect("sign-core", sign.transform, Vector2.zero, new Vector2(0.16f, 0.16f), Color.white, 22);

            PixelPart.Rect("sign-glow", sign.transform, Vector2.zero, new Vector2(0.82f, 0.62f), new Color(accent.r, accent.g, accent.b, 0.2f), 20);
        }

        private void BuildRoomProps(string id, Transform parent, Color accent)
        {
            PixelPart.Rect("shelf", parent, new Vector2(-1.05f, 0.78f), new Vector2(0.9f, 0.08f), new Color(0.37f, 0.2f, 0.13f), 12);
            PixelPart.Rect("book-a", parent, new Vector2(-1.32f, 0.95f), new Vector2(0.14f, 0.32f), accent, 13);
            PixelPart.Rect("book-b", parent, new Vector2(-1.12f, 0.93f), new Vector2(0.14f, 0.36f), new Color(0.91f, 0.65f, 0.25f), 13);
            PixelPart.Rect("box", parent, new Vector2(-0.82f, 0.9f), new Vector2(0.26f, 0.2f), new Color(0.6f, 0.38f, 0.18f), 13);
            PixelPart.Rect("plant-pot", parent, new Vector2(-1.32f, -0.76f), new Vector2(0.26f, 0.26f), new Color(0.56f, 0.3f, 0.18f), 16);
            PixelPart.Rect("plant-leaf-a", parent, new Vector2(-1.4f, -0.46f), new Vector2(0.18f, 0.42f), new Color(0.27f, 0.8f, 0.38f), 17);
            PixelPart.Rect("plant-leaf-b", parent, new Vector2(-1.22f, -0.42f), new Vector2(0.18f, 0.5f), new Color(0.38f, 0.93f, 0.49f), 17);

            switch (id)
            {
                case "router":
                    PixelPart.Rect("crown-base", parent, new Vector2(0f, 1.08f), new Vector2(0.52f, 0.14f), new Color(1f, 0.82f, 0.35f), 14);
                    PixelPart.Rect("crown-mid", parent, new Vector2(0f, 1.25f), new Vector2(0.16f, 0.32f), new Color(1f, 0.82f, 0.35f), 14);
                    break;
                case "multi":
                    for (var i = 0; i < 5; i++)
                    {
                        PixelPart.Rect($"code-line-{i}", parent, new Vector2(-0.1f, 0.96f - i * 0.12f), new Vector2(0.8f - i * 0.08f, 0.04f), i % 2 == 0 ? accent : Color.white, 14);
                    }
                    break;
                case "ardida":
                    PixelPart.Rect("palette", parent, new Vector2(0f, 0.92f), new Vector2(0.62f, 0.34f), Color.white, 14);
                    PixelPart.Rect("paint-a", parent, new Vector2(-0.16f, 0.96f), new Vector2(0.12f, 0.12f), accent, 15);
                    PixelPart.Rect("paint-b", parent, new Vector2(0.08f, 0.92f), new Vector2(0.12f, 0.12f), new Color(1f, 0.82f, 0.35f), 15);
                    break;
                case "prpagyda":
                    PixelPart.Rect("chart-board", parent, new Vector2(0f, 0.9f), new Vector2(0.72f, 0.44f), new Color(0.92f, 0.95f, 0.84f), 14);
                    PixelPart.Rect("chart-a", parent, new Vector2(-0.2f, 0.82f), new Vector2(0.1f, 0.22f), new Color(1f, 0.4f, 0.4f), 15);
                    PixelPart.Rect("chart-b", parent, new Vector2(0f, 0.9f), new Vector2(0.1f, 0.34f), accent, 15);
                    PixelPart.Rect("chart-c", parent, new Vector2(0.2f, 0.96f), new Vector2(0.1f, 0.46f), new Color(0.47f, 0.94f, 0.61f), 15);
                    break;
                default:
                    PixelPart.Rect("question", parent, new Vector2(0f, 0.96f), new Vector2(0.38f, 0.5f), accent, 14);
                    PixelPart.Rect("question-hole", parent, new Vector2(0.04f, 0.82f), new Vector2(0.12f, 0.08f), Color.white, 15);
                    break;
            }
        }

        private void BuildSofa(string name, Vector2 position, bool flip)
        {
            var sofa = new GameObject(name);
            sofa.transform.SetParent(sceneRoot, false);
            sofa.transform.localPosition = position;
            sofa.transform.localScale = new Vector3(flip ? -1f : 1f, 1f, 1f);
            PixelPart.Rect("base", sofa.transform, Vector2.zero, new Vector2(1.12f, 0.42f), new Color(0.12f, 0.28f, 0.54f), 12);
            PixelPart.Rect("back", sofa.transform, new Vector2(0, 0.24f), new Vector2(1.0f, 0.28f), new Color(0.15f, 0.34f, 0.64f), 13);
            PixelPart.Rect("cushion-a", sofa.transform, new Vector2(-0.28f, 0.02f), new Vector2(0.38f, 0.22f), new Color(0.2f, 0.42f, 0.72f), 14);
            PixelPart.Rect("cushion-b", sofa.transform, new Vector2(0.28f, 0.02f), new Vector2(0.38f, 0.22f), new Color(0.2f, 0.42f, 0.72f), 14);
        }

        private static Vector2 IsoToWorld(int x, int y)
        {
            return new Vector2((x - y) * 0.48f, (x + y) * 0.24f);
        }

        private void OnSceneStateReceived(SceneState state)
        {
            var route = state?.routeTarget ?? "";
            if (route == currentRoute)
            {
                return;
            }

            foreach (var character in characters.Values)
            {
                character.SetReceiving(false);
            }

            currentRoute = route;
            if (string.IsNullOrEmpty(route) || !roomCenters.TryGetValue(route, out var target))
            {
                return;
            }

            characters[route].SetReceiving(true);
            packet.Fly(Vector3.zero, routeTargets[route], accents[route]);
        }
    }
}
