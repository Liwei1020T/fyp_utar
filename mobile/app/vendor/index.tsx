import React from 'react';
import { Redirect } from 'expo-router';

export default function LegacyAdminIndexRedirect() {
  return <Redirect href="/admin/dashboard" />;
}
