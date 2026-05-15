using System;
using System.Collections;
using UnityEngine;
using UnityEngine.Networking;

namespace TelegramOffice
{
    public sealed class RouterApiClient : MonoBehaviour
    {
        [SerializeField] private string sceneStateUrl = "http://127.0.0.1:8000/scene-state";
        [SerializeField] private float pollSeconds = 1.25f;

        public event Action<SceneState> SceneStateReceived;

        private void OnEnable()
        {
            StartCoroutine(Poll());
        }

        private IEnumerator Poll()
        {
            var wait = new WaitForSeconds(pollSeconds);
            while (enabled)
            {
                using var request = UnityWebRequest.Get(sceneStateUrl);
                yield return request.SendWebRequest();

                if (request.result == UnityWebRequest.Result.Success)
                {
                    var state = JsonUtility.FromJson<SceneState>(request.downloadHandler.text);
                    SceneStateReceived?.Invoke(state);
                }

                yield return wait;
            }
        }
    }
}

