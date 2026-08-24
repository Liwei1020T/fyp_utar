import React from 'react';
import { Tabs } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { BarChart3, Boxes, CalendarRange, LayoutDashboard, MessageCircleMore } from 'lucide-react-native';
import { Platform, View } from 'react-native';
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
    <View className="h-8 w-8 items-center justify-center">
      <Icon size={size} color={color} strokeWidth={focused ? 2.1 : 1.9} />
    </View>
  );
}

export default function AdminTabsLayout() {
  const insets = useSafeAreaInsets();
  const bottomSpacing = Math.max(insets.bottom, 10);
  const tabBarHeight = 66 + bottomSpacing;

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        sceneStyle: {
          backgroundColor: appChromeColors.pageAdmin,
        },
        tabBarHideOnKeyboard: true,
        tabBarActiveTintColor: appChromeColors.heroDeep,
        tabBarInactiveTintColor: '#C7D1E0',
        tabBarActiveBackgroundColor: appChromeColors.tabBarActive,
        tabBarStyle: {
          backgroundColor: appChromeColors.tabBar,
          borderTopWidth: 0,
          height: tabBarHeight,
          paddingBottom: bottomSpacing,
          paddingTop: 8,
          paddingHorizontal: 2,
          marginHorizontal: 12,
          marginBottom: bottomSpacing,
          borderRadius: 16,
          ...(Platform.OS === 'web'
            ? { boxShadow: '0 14px 32px rgba(9, 29, 62, 0.22)' }
            : {
                shadowColor: '#091D3E',
                shadowOpacity: 0.2,
                shadowOffset: { width: 0, height: 10 },
                shadowRadius: 20,
                elevation: 12,
              }),
          overflow: 'hidden',
        },
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: '600',
          marginTop: 0,
        },
        tabBarItemStyle: {
          minHeight: 48,
          marginHorizontal: 0,
          marginVertical: 1,
          borderRadius: 10,
          overflow: 'hidden',
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
