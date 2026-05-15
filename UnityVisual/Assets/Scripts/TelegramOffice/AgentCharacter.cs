using UnityEngine;

namespace TelegramOffice
{
    public sealed class AgentCharacter : MonoBehaviour
    {
        private string agentId;
        private Color accent;
        private Vector3 startPosition;
        private bool receiving;
        private Transform leftArm;
        private Transform rightArm;
        private Transform laptop;
        private Transform laptopLogo;
        private Transform headphoneLeft;
        private Transform headphoneRight;
        private Transform hairTop;
        private Transform hoodieGlow;

        public void Build(string id, Color skin, Color hair, Color hoodie, Color accentColor)
        {
            agentId = id;
            accent = accentColor;
            startPosition = transform.localPosition;

            PixelPart.Rect("shadow", transform, new Vector2(0.05f, -1.55f), new Vector2(2.4f, 0.22f), new Color(0, 0, 0, 0.25f), 20);
            PixelPart.Rect("left-shoe", transform, new Vector2(-0.48f, -1.32f), new Vector2(0.52f, 0.24f), accentColor, 30);
            PixelPart.Rect("right-shoe", transform, new Vector2(0.48f, -1.32f), new Vector2(0.62f, 0.24f), accentColor, 30);
            PixelPart.Rect("left-leg", transform, new Vector2(-0.38f, -0.9f), new Vector2(0.36f, 0.72f), new Color(0.13f, 0.14f, 0.2f), 31);
            PixelPart.Rect("right-leg", transform, new Vector2(0.34f, -0.9f), new Vector2(0.38f, 0.72f), new Color(0.13f, 0.14f, 0.2f), 31);

            PixelPart.Rect("hoodie", transform, new Vector2(0, -0.2f), new Vector2(1.25f, 0.95f), hoodie, 34);
            PixelPart.Rect("hoodie-shade", transform, new Vector2(0, -0.58f), new Vector2(1.05f, 0.18f), hoodie * 0.75f, 35);
            PixelPart.Rect("zip", transform, new Vector2(0.02f, -0.18f), new Vector2(0.06f, 0.72f), accentColor, 36);
            hoodieGlow = PixelPart.Rect("hoodie-symbol", transform, new Vector2(0, -0.12f), new Vector2(0.34f, 0.2f), accentColor, 38).transform;
            leftArm = PixelPart.Rect("left-arm", transform, new Vector2(-0.82f, -0.28f), new Vector2(0.32f, 0.86f), hoodie, 33).transform;
            rightArm = PixelPart.Rect("right-arm", transform, new Vector2(0.88f, -0.18f), new Vector2(0.3f, 0.72f), hoodie, 33).transform;

            PixelPart.Rect("neck", transform, new Vector2(0, 0.35f), new Vector2(0.34f, 0.26f), skin * 0.9f, 36);
            PixelPart.Rect("head", transform, new Vector2(0, 0.82f), new Vector2(1.05f, 0.82f), skin, 39);
            PixelPart.Rect("hair-back", transform, new Vector2(0, 1.08f), new Vector2(1.32f, 0.48f), hair, 42);
            PixelPart.Rect("hair-left", transform, new Vector2(-0.42f, 1.26f), new Vector2(0.52f, 0.3f), hair * 0.85f, 43);
            hairTop = PixelPart.Rect("hair-top", transform, new Vector2(0.12f, 1.38f), new Vector2(0.82f, 0.26f), hair, 43).transform;
            PixelPart.Rect("hair-spike-a", transform, new Vector2(-0.58f, 1.44f), new Vector2(0.24f, 0.2f), hair * 0.9f, 44);
            PixelPart.Rect("hair-spike-b", transform, new Vector2(0.46f, 1.42f), new Vector2(0.32f, 0.18f), hair * 0.92f, 44);
            PixelPart.Rect("left-eye", transform, new Vector2(-0.24f, 0.88f), new Vector2(0.12f, 0.12f), Color.white, 44);
            PixelPart.Rect("right-eye", transform, new Vector2(0.24f, 0.88f), new Vector2(0.12f, 0.12f), Color.white, 44);
            PixelPart.Rect("left-pupil", transform, new Vector2(-0.22f, 0.88f), new Vector2(0.06f, 0.08f), Color.black, 45);
            PixelPart.Rect("right-pupil", transform, new Vector2(0.26f, 0.88f), new Vector2(0.06f, 0.08f), Color.black, 45);
            PixelPart.Rect("glasses-l", transform, new Vector2(-0.24f, 0.88f), new Vector2(0.3f, 0.22f), new Color(0.04f, 0.05f, 0.08f), 46);
            PixelPart.Rect("glasses-r", transform, new Vector2(0.24f, 0.88f), new Vector2(0.3f, 0.22f), new Color(0.04f, 0.05f, 0.08f), 46);
            PixelPart.Rect("smile", transform, new Vector2(0.04f, 0.62f), new Vector2(0.22f, 0.05f), new Color(0.55f, 0.21f, 0.18f), 46);

            headphoneLeft = PixelPart.Rect("headphone-l", transform, new Vector2(-0.5f, 0.22f), new Vector2(0.28f, 0.36f), new Color(0.05f, 0.06f, 0.09f), 48).transform;
            headphoneRight = PixelPart.Rect("headphone-r", transform, new Vector2(0.5f, 0.22f), new Vector2(0.28f, 0.36f), new Color(0.05f, 0.06f, 0.09f), 48).transform;
            PixelPart.Rect("headphone-light-l", transform, new Vector2(-0.5f, 0.22f), new Vector2(0.12f, 0.16f), accentColor, 49);
            PixelPart.Rect("headphone-light-r", transform, new Vector2(0.5f, 0.22f), new Vector2(0.12f, 0.16f), accentColor, 49);
            laptop = PixelPart.Rect("laptop", transform, new Vector2(0.96f, -0.02f), new Vector2(0.78f, 0.52f), new Color(0.16f, 0.15f, 0.2f), 50).transform;
            laptopLogo = PixelPart.Rect("laptop-logo", transform, new Vector2(0.98f, 0f), new Vector2(0.16f, 0.08f), accentColor, 51).transform;
        }

        public void SetReceiving(bool value)
        {
            receiving = value;
        }

        private void Update()
        {
            var seed = Mathf.Abs(agentId.GetHashCode() % 31) * 0.03f;
            var frame = Mathf.FloorToInt((Time.time + seed) * 6f) % 4;
            var bob = frame is 1 or 2 ? 0.045f : 0f;
            var pulse = receiving ? Mathf.Sin(Time.time * 12f) * 0.08f : 0f;
            transform.localPosition = startPosition + Vector3.up * (bob + Mathf.Abs(pulse));
            transform.localScale = Vector3.one * (receiving ? 1.06f : 1f);

            var typingOffset = frame is 0 or 3 ? 0f : 0.055f;
            leftArm.localPosition = new Vector3(-0.82f, -0.28f - typingOffset, 0f);
            rightArm.localPosition = new Vector3(0.88f, -0.18f + typingOffset, 0f);
            laptop.localPosition = new Vector3(0.96f, -0.02f + typingOffset * 0.4f, 0f);
            laptopLogo.localPosition = new Vector3(0.98f, typingOffset * 0.4f, 0f);
            hairTop.localPosition = new Vector3(0.12f, 1.38f + bob * 0.5f, 0f);
            headphoneLeft.localScale = Vector3.one * (receiving ? 1.14f : 1f);
            headphoneRight.localScale = Vector3.one * (receiving ? 1.14f : 1f);
            hoodieGlow.localScale = Vector3.one * (receiving ? 1.25f : 1f);
        }
    }
}
