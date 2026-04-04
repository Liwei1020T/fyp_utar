import React from 'react';
import { RoleGuard } from '../../components/roles/RoleGuard';

export default function VendorLayout() {
  return <RoleGuard role="vendor" />;
}
