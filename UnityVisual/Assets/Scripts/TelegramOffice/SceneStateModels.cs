using System;

namespace TelegramOffice
{
    [Serializable]
    public class SceneState
    {
        public string routeTarget;
        public string latestText;
        public AgentInfo[] agents;
        public RouterEvent[] events;
    }

    [Serializable]
    public class AgentInfo
    {
        public string id;
        public string name;
        public string telegram;
        public string kind;
        public string role;
    }

    [Serializable]
    public class RouterEvent
    {
        public string timestamp;
        public string direction;
        public string actor;
        public string text;
    }
}

