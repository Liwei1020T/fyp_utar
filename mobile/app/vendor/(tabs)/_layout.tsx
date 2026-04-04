import React from 'react';
import { Tabs } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { BarChart3, Boxes, CalendarRange, LayoutDashboard, MessageCircleMore } from 'lucide-react-native';
import { View } from 'react-native';
import { HeroText, cn } from '../../../components/ui/heroui';
import { appChromeColors, appLayoutMetrics } from '../../../components/ui/theme';

function VendorTabIcon({
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
        'h-10 w-10 items-center justify-center rounded-2xl',
        focused ? 'bg-control-50' : 'bg-transparent'
      )}
    >
      <Icon size={size} color={color} strokeWidth={focused ? 2.1 : 1.9} />
    </View>
  );
}

export default function VendorTabsLayout() {
  const insets = useSafeAreaInsets();
  const tabBarHeight = 74 + Math.max(insets.bottom, 10);

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        sceneStyle: { backgroundColor: appChromeColors.pageVendor },
        tabBarHideOnKeyboard: true,
        tabBarActiveTintColor: '#22766D',
        tabBarInactiveTintColor: appChromeColors.inactive,
        tabBarStyle: {
          backgroundColor: appChromeColors.tabBar,
          borderWidth: 1,
          borderColor: appChromeColors.tabBarBorder,
          height: tabBarHeight,
          paddingBottom: Math.max(insets.bottom, 10),
          paddingTop: 10,
          position: 'absolute',
          left: appLayoutMetrics.pagePadding,
          right: appLayoutMetrics.pagePadding,
          bottom: Math.max(insets.bottom, 10),
          borderRadius: 32,
          shadowColor: '#14233C',
          shadowOpacity: 0.1,
          shadowOffset: { width: 0, height: 12 },
          shadowRadius: 24,
          elevation: 10,
          overflow: 'hidden',
        },
        tabBarLabelStyle: {
          fontSize: 11,
          fontWeight: '700',
          marginTop: 2,
        },
      }}
    >
      <Tabs.Screen
        name="dashboard"
        options={{
          title: 'Overview',
          tabBarIcon: ({ color, size, focused }) => (
            <VendorTabIcon icon={LayoutDashboard} color={color} size={size} focused={focused} />
          ),
        }}
      />
      <Tabs.Screen
        name="bookings"
        options={{
          title: 'Bookings',
          tabBarIcon: ({ color, size, focused }) => (
            <VendorTabIcon icon={CalendarRange} color={color} size={size} focused={focused} />
          ),
        }}
      />
      <Tabs.Screen
        name="inventory"
        options={{
          title: 'Inventory',
          tabBarIcon: ({ color, size, focused }) => (
            <VendorTabIcon icon={Boxes} color={color} size={size} focused={focused} />
          ),
        }}
      />
      <Tabs.Screen
        name="chat"
        options={{
          title: 'Chat',
          tabBarIcon: ({ color, size, focused }) => (
            <VendorTabIcon icon={MessageCircleMore} color={color} size={size} focused={focused} />
          ),
        }}
      />
      <Tabs.Screen
        name="analytics"
        options={{
          title: 'Analytics',
          tabBarIcon: ({ color, size, focused }) => (
            <VendorTabIcon icon={BarChart3} color={color} size={size} focused={focused} />
          ),
        }}
      />
    </Tabs>
  );
}
