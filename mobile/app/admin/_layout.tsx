import React from 'react';
import { RoleGuard } from '../../components/roles/RoleGuard';

export default function AdminLayout() {
  return <RoleGuard role="admin" />;
}
