using UnityEngine;

namespace TelegramOffice
{
    public static class PixelPart
    {
        public static GameObject Rect(string name, Transform parent, Vector2 localPosition, Vector2 size, Color color, int sortingOrder)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = localPosition;
            go.transform.localScale = new Vector3(size.x, size.y, 1f);

            var renderer = go.AddComponent<SpriteRenderer>();
            renderer.sprite = PixelSpriteFactory.Solid(color);
            renderer.sortingOrder = sortingOrder;
            return go;
        }

        public static GameObject Diamond(
            string name,
            Transform parent,
            Vector2 localPosition,
            Vector2 size,
            Color fill,
            Color edge,
            int sortingOrder)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = localPosition;
            go.transform.localScale = new Vector3(size.x, size.y, 1f);

            var renderer = go.AddComponent<SpriteRenderer>();
            renderer.sprite = PixelSpriteFactory.Diamond(fill, edge);
            renderer.sortingOrder = sortingOrder;
            return go;
        }
    }
}
