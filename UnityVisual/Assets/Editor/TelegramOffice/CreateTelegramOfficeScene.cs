using System.IO;
using TelegramOffice;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

public static class CreateTelegramOfficeScene
{
    public const string ScenePath = "Assets/Scenes/TelegramOffice.unity";

    [MenuItem("Tools/Telegram Office/Create Visualizer Scene")]
    public static void CreateScene()
    {
        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        var bootstrap = new GameObject("Telegram Office Bootstrap");
        bootstrap.AddComponent<TelegramOfficeScene>();

        Directory.CreateDirectory("Assets/Scenes");
        EditorSceneManager.SaveScene(scene, ScenePath);
        Selection.activeGameObject = bootstrap;
    }

    [MenuItem("Tools/Telegram Office/Rebuild Lobby Preview")]
    public static void RebuildLobbyPreview()
    {
        if (EditorSceneManager.GetActiveScene().path != ScenePath)
        {
            EditorSceneManager.OpenScene(ScenePath);
        }

        var visualizer = Object.FindFirstObjectByType<TelegramOfficeScene>();
        if (visualizer == null)
        {
            var bootstrap = GameObject.Find("Telegram Office Bootstrap") ?? new GameObject("Telegram Office Bootstrap");
            visualizer = bootstrap.AddComponent<TelegramOfficeScene>();
        }

        visualizer.EnsureScene();
        EditorSceneManager.MarkSceneDirty(EditorSceneManager.GetActiveScene());
        EditorSceneManager.SaveScene(EditorSceneManager.GetActiveScene());
        Selection.activeGameObject = visualizer.gameObject;
    }
}
