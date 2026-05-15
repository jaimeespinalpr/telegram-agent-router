using UnityEngine;

namespace TelegramOffice
{
    public static class PixelSpriteFactory
    {
        public static Sprite Solid(Color color, int width = 16, int height = 16)
        {
            var texture = new Texture2D(width, height, TextureFormat.RGBA32, false)
            {
                filterMode = FilterMode.Point
            };

            var pixels = new Color[width * height];
            for (var i = 0; i < pixels.Length; i++)
            {
                pixels[i] = color;
            }

            texture.SetPixels(pixels);
            texture.Apply();
            return Sprite.Create(texture, new Rect(0, 0, width, height), new Vector2(0.5f, 0.5f), 16);
        }

        public static Sprite Diamond(Color fill, Color edge, int width = 32, int height = 18)
        {
            var texture = new Texture2D(width, height, TextureFormat.RGBA32, false)
            {
                filterMode = FilterMode.Point
            };

            var transparent = new Color(0, 0, 0, 0);
            var centerX = (width - 1) * 0.5f;
            var centerY = (height - 1) * 0.5f;
            for (var y = 0; y < height; y++)
            {
                for (var x = 0; x < width; x++)
                {
                    var distance = Mathf.Abs((x - centerX) / centerX) + Mathf.Abs((y - centerY) / centerY);
                    var color = transparent;
                    if (distance <= 1f)
                    {
                        color = distance > 0.82f ? edge : fill;
                    }

                    texture.SetPixel(x, y, color);
                }
            }

            texture.Apply();
            return Sprite.Create(texture, new Rect(0, 0, width, height), new Vector2(0.5f, 0.5f), 16);
        }
    }
}
