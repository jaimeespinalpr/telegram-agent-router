using System.IO;
using TelegramOffice;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

[InitializeOnLoad]
public static class TelegramOfficeAutoSetup
{
    static TelegramOfficeAutoSetup()
    {
        EditorApplication.delayCall += EnsureScene;
    }

    private static void EnsureScene()
    {
        if (!File.Exists(CreateTelegramOfficeScene.ScenePath))
        {
            CreateTelegramOfficeScene.CreateScene();
            return;
        }

        if (EditorSceneManager.GetActiveScene().path != CreateTelegramOfficeScene.ScenePath)
        {
            EditorSceneManager.OpenScene(CreateTelegramOfficeScene.ScenePath);
        }

        var existing = Object.FindFirstObjectByType<TelegramOfficeScene>();
        if (existing != null)
        {
            existing.EnsureScene();
            EditorSceneManager.MarkSceneDirty(EditorSceneManager.GetActiveScene());
            return;
        }

        var bootstrap = GameObject.Find("Telegram Office Bootstrap") ?? new GameObject("Telegram Office Bootstrap");
        bootstrap.AddComponent<TelegramOfficeScene>();
        EditorSceneManager.MarkSceneDirty(EditorSceneManager.GetActiveScene());
        EditorSceneManager.SaveScene(EditorSceneManager.GetActiveScene());
    }
}
