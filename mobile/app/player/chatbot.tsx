import React from 'react';
import { Redirect } from 'expo-router';

export default function LegacyChatbotRedirect() {
  return <Redirect href="/player/chat" />;
}
