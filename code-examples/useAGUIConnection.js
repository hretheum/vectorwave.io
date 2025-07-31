# React AG-UI Integration Hook

```javascript
// src/frontend/hooks/useAGUIConnection.js
import { useEffect, useState, useCallback } from 'react';
import { AGUIClient } from '../services/aguiClient';

export const useAGUIConnection = () => {
  const [topics, setTopics] = useState([]);
  const [agentStatus, setAgentStatus] = useState({});
  const [pendingDecisions, setPendingDecisions] = useState([]);
  const [isConnected, setIsConnected] = useState(false);
  const [activities, setActivities] = useState([]);
  const [client] = useState(() => new AGUIClient('/api/agui/stream'));

  useEffect(() => {
    // Connect to AG-UI stream
    client.connect();

    // Connection event handlers
    client.on('connect', () => {
      setIsConnected(true);
      console.log('🔌 Connected to AG-UI stream');
    });

    client.on('disconnect', () => {
      setIsConnected(false);
      console.log('❌ Disconnected from AG-UI stream');
    });

    client.on('error', (error) => {
      console.error('AG-UI Connection Error:', error);
    });

    // Topic discovery events
    client.on('topic_discovered', (event) => {
      const newTopic = {
        ...event.data.topic,
        status: 'discovered',
        agent_id: event.agent_id,
        timestamp: event.timestamp
      };
      
      setTopics(prev => {
        // Avoid duplicates
        const exists = prev.find(t => t.id === newTopic.id);
        if (exists) return prev;
        return [...prev, newTopic];
      });

      // Add to activity feed
      setActivities(prev => [{
        id: Date.now(),
        type: 'topic_discovered',
        message: `📰 Nowy temat: ${newTopic.title}`,
        agent: event.agent_id,
        timestamp: event.timestamp
      }, ...prev.slice(0, 49)]); // Keep last 50 activities
    });
```
    // Content analysis events
    client.on('content_analysis', (event) => {
      setTopics(prev => prev.map(topic => 
        topic.id === event.data.topic_id 
          ? { 
              ...topic, 
              analysis: event.data.analysis,
              ai_recommendation: event.data.ai_recommendation,
              confidence_score: event.data.confidence_score,
              status: 'analyzed'
            }
          : topic
      ));

      setActivities(prev => [{
        id: Date.now(),
        type: 'analysis_complete',
        message: `📊 Analiza: ${event.data.topic_title}`,
        agent: event.agent_id,
        timestamp: event.timestamp
      }, ...prev.slice(0, 49)]);
    });

    // Human input requests
    client.on('human_input_request', (event) => {
      const decision = {
        id: event.data.topic_id || Date.now(),
        topic_id: event.data.topic_id,
        topic_title: event.data.topic_title,
        controversy_reason: event.data.controversy_reason,
        ai_recommendation: event.data.ai_recommendation,
        options: event.data.options,
        timeout: event.data.timeout,
        priority: event.data.priority || 'medium',
        requested_at: new Date().toISOString()
      };

      setPendingDecisions(prev => [...prev, decision]);

      setActivities(prev => [{
        id: Date.now(),
        type: 'human_input_needed',
        message: `🤔 Wymagana decyzja: ${decision.topic_title}`,
        agent: event.agent_id,
        timestamp: event.timestamp,
        priority: decision.priority
      }, ...prev.slice(0, 49)]);
    });
```
    // Editorial decisions
    client.on('editorial_decision', (event) => {
      setTopics(prev => prev.map(topic =>
        topic.id === event.data.topic_id
          ? {
              ...topic,
              decision: event.data.decision,
              reasoning: event.data.reasoning,
              human_override: event.data.human_override,
              final_score: event.data.final_score,
              priority: event.data.priority,
              status: 'decided'
            }
          : topic
      ));

      // Remove from pending decisions if it was there
      setPendingDecisions(prev => 
        prev.filter(d => d.topic_id !== event.data.topic_id)
      );

      const icon = event.data.decision === 'approve' ? '✅' : 
                   event.data.decision === 'reject' ? '❌' : '⏳';
      
      setActivities(prev => [{
        id: Date.now(),
        type: 'decision_made',
        message: `${icon} Decyzja: ${event.data.decision}`,
        agent: event.agent_id,
        timestamp: event.timestamp
      }, ...prev.slice(0, 49)]);
    });

    // Progress updates
    client.on('progress_update', (event) => {
      setAgentStatus(prev => ({
        ...prev,
        [event.agent_id]: {
          ...prev[event.agent_id],
          stage: event.data.stage,
          message: event.data.message,
          progress: event.data.progress,
          last_update: event.timestamp
        }
      }));
    });
```