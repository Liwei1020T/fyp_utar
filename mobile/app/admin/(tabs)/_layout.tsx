import React from 'react';
import { Tabs } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { BarChart3, Boxes, CalendarRange, LayoutDashboard, MessageCircleMore } from 'lucide-react-native';
import { Platform, View } from 'react-native';
import { cn } from '../../../components/ui/heroui';
import { appChromeColors } from '../../../components/ui/theme';

function AdminTabIcon({
  icon: Icon,
  color,
  size,
  focused,
}: {
  icon: typeof LayoutDashboard;
  color: string;
  size: number;
  focused: boolean;
}) {
  return (
    <View
      className={cn(
        'h-9 w-9 items-center justify-center rounded-[10px]',
        focused ? 'bg-secondary-50' : 'bg-transparent'
      )}
    >
      <Icon size={size} color={color} strokeWidth={focused ? 2.1 : 1.9} />
    </View>
  );
}

export default function AdminTabsLayout() {
  const insets = useSafeAreaInsets();
  const tabBarHeight = 60 + Math.max(insets.bottom, 8);

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        sceneStyle: {
          backgroundColor: appChromeColors.pageAdmin,
        },
        tabBarHideOnKeyboard: true,
        tabBarActiveTintColor: appChromeColors.primary,
        tabBarInactiveTintColor: appChromeColors.inactive,
        tabBarStyle: {
          backgroundColor: appChromeColors.tabBar,
          borderTopColor: appChromeColors.tabBarBorder,
          height: tabBarHeight,
          paddingBottom: Math.max(insets.bottom, 8),
          paddingTop: 7,
          marginHorizontal: 0,
          marginBottom: 0,
          borderRadius: 0,
          ...(Platform.OS === 'web'
            ? { boxShadow: '0 -4px 14px rgba(15, 23, 42, 0.05)' }
            : {
                shadowColor: '#14181F',
                shadowOpacity: 0.06,
                shadowOffset: { width: 0, height: -4 },
                shadowRadius: 14,
                elevation: 8,
              }),
          overflow: 'hidden',
        },
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: '600',
          marginTop: 1,
        },
      }}
    >
      <Tabs.Screen
        name="dashboard"
        options={{
          title: 'Overview',
          tabBarIcon: ({ color, size, focused }) => (
            <AdminTabIcon icon={LayoutDashboard} color={color} size={size} focused={focused} />
          ),
        }}
      />
      <Tabs.Screen
        name="bookings"
        options={{
          title: 'Bookings',
          tabBarIcon: ({ color, size, focused }) => (
            <AdminTabIcon icon={CalendarRange} color={color} size={size} focused={focused} />
          ),
        }}
      />
      <Tabs.Screen
        name="inventory"
        options={{
          title: 'Inventory',
          tabBarIcon: ({ color, size, focused }) => (
            <AdminTabIcon icon={Boxes} color={color} size={size} focused={focused} />
          ),
        }}
      />
      <Tabs.Screen
        name="chat"
        options={{
          title: 'Chat',
          tabBarIcon: ({ color, size, focused }) => (
            <AdminTabIcon icon={MessageCircleMore} color={color} size={size} focused={focused} />
          ),
        }}
      />
      <Tabs.Screen
        name="analytics"
        options={{
          title: 'Analytics',
          tabBarIcon: ({ color, size, focused }) => (
            <AdminTabIcon icon={BarChart3} color={color} size={size} focused={focused} />
          ),
        }}
      />
    </Tabs>
  );
}
