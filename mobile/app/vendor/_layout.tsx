import React from 'react';
import { Redirect, usePathname } from 'expo-router';

export default function VendorLayout() {
  const pathname = usePathname();
  const nextPath = pathname.replace(/^\/vendor/, '/admin') || '/admin';

  return <Redirect href={nextPath as never} />;
}
