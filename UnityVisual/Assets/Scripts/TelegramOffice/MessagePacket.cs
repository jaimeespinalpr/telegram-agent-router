using UnityEngine;

namespace TelegramOffice
{
    public sealed class MessagePacket : MonoBehaviour
    {
        private Vector3 from;
        private Vector3 to;
        private float startedAt;
        private SpriteRenderer body;
        private SpriteRenderer trail;
        private SpriteRenderer trailFar;
        private Color accentColor;

        public void Build()
        {
            body = PixelPart.Rect("packet-body", transform, Vector2.zero, new Vector2(0.55f, 0.32f), new Color(1f, 0.93f, 0.75f), 100).GetComponent<SpriteRenderer>();
            trail = PixelPart.Rect("packet-trail", transform, new Vector2(-0.55f, 0), new Vector2(0.38f, 0.08f), Color.cyan, 99).GetComponent<SpriteRenderer>();
            trailFar = PixelPart.Rect("packet-trail-far", transform, new Vector2(-0.92f, 0), new Vector2(0.22f, 0.06f), Color.white, 98).GetComponent<SpriteRenderer>();
            gameObject.SetActive(false);
        }

        public void Fly(Vector3 start, Vector3 end, Color accent)
        {
            from = start;
            to = end;
            startedAt = Time.time;
            accentColor = accent;
            body.color = new Color(1f, 0.93f, 0.75f);
            trail.color = accent;
            trailFar.color = new Color(accent.r, accent.g, accent.b, 0.55f);
            gameObject.SetActive(true);
        }

        private void Update()
        {
            var t = Mathf.Repeat(Time.time - startedAt, 2.2f) / 2.2f;
            var eased = Mathf.SmoothStep(0f, 1f, t);
            transform.position = Vector3.Lerp(from, to, eased) + Vector3.up * Mathf.Sin(eased * Mathf.PI) * 0.45f;
            var direction = to - from;
            if (direction.sqrMagnitude > 0.01f)
            {
                var angle = Mathf.Atan2(direction.y, direction.x) * Mathf.Rad2Deg;
                transform.rotation = Quaternion.Euler(0, 0, angle);
            }

            var pulse = 0.92f + Mathf.Sin(Time.time * 14f) * 0.08f;
            transform.localScale = Vector3.one * pulse;
            trail.color = Color.Lerp(accentColor, Color.white, Mathf.PingPong(Time.time * 3f, 1f) * 0.35f);
        }
    }
}
