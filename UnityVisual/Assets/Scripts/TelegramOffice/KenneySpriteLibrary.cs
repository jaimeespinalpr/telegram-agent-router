using System.Collections.Generic;
using UnityEngine;

namespace TelegramOffice
{
    public static class KenneySpriteLibrary
    {
        private const string Root = "Kenney/IsometricMiniaturePrototype/Angle/";
        private static readonly Dictionary<string, Sprite> Cache = new();

        public static bool Has(string assetName)
        {
            return Get(assetName) != null;
        }

        public static GameObject Place(
            string name,
            Transform parent,
            string assetName,
            Vector2 localPosition,
            float scale,
            int sortingOrder,
            Color? tint = null)
        {
            var sprite = Get(assetName);
            if (sprite == null)
            {
                return null;
            }

            var item = new GameObject(name);
            item.transform.SetParent(parent, false);
            item.transform.localPosition = localPosition;
            item.transform.localScale = Vector3.one * scale;

            var renderer = item.AddComponent<SpriteRenderer>();
            renderer.sprite = sprite;
            renderer.sortingOrder = sortingOrder;
            renderer.color = tint ?? Color.white;
            return item;
        }

        private static Sprite Get(string assetName)
        {
            if (Cache.TryGetValue(assetName, out var sprite))
            {
                return sprite;
            }

            var texture = Resources.Load<Texture2D>(Root + assetName);
            if (texture == null)
            {
                Cache[assetName] = null;
                return null;
            }

            texture.filterMode = FilterMode.Point;
            texture.wrapMode = TextureWrapMode.Clamp;

            sprite = Sprite.Create(
                texture,
                new Rect(0, 0, texture.width, texture.height),
                new Vector2(0.5f, 0.28f),
                170f,
                0,
                SpriteMeshType.FullRect);
            sprite.name = assetName;
            Cache[assetName] = sprite;
            return sprite;
        }
    }
}
