#if UNITY_EDITOR
using UnityEditor;

namespace TelegramOffice.Editor
{
    public sealed class KenneyTextureImporter : AssetPostprocessor
    {
        private void OnPreprocessTexture()
        {
            if (!assetPath.StartsWith("Assets/Resources/Kenney/"))
            {
                return;
            }

            var importer = (TextureImporter)assetImporter;
            importer.textureType = TextureImporterType.Default;
            importer.mipmapEnabled = false;
            importer.filterMode = UnityEngine.FilterMode.Point;
            importer.textureCompression = TextureImporterCompression.Uncompressed;
            importer.alphaIsTransparency = true;
        }
    }
}
#endif
