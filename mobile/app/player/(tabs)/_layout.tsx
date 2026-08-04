import React from 'react';
import { Tabs } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Calendar, Home, List, User, Zap } from 'lucide-react-native';
import { Platform, View } from 'react-native';
import { cn } from '../../../components/ui/heroui';
import { appChromeColors } from '../../../components/ui/theme';

function StandardTabIcon({
  icon: Icon,
  color,
  size,
  focused,
}: {
  icon: typeof Home;
  color: string;
  size: number;
  focused: boolean;
}) {
  return (
    <View
      className={cn(
        'h-9 w-9 items-center justify-center rounded-[10px]',
        focused ? 'bg-primary-50' : 'bg-transparent'
      )}
    >
      <Icon size={size} color={color} strokeWidth={focused ? 2.1 : 1.9} />
    </View>
  );
}

export default function TabsLayout() {
  const insets = useSafeAreaInsets();
  const tabBarHeight = 60 + Math.max(insets.bottom, 8);

  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        sceneStyle: {
          backgroundColor: appChromeColors.page,
        },
        tabBarHideOnKeyboard: true,
        tabBarActiveTintColor: appChromeColors.primary,
        tabBarInactiveTintColor: appChromeColors.inactive,
        tabBarStyle: {
          backgroundColor: appChromeColors.tabBar,
          borderTopColor: appChromeColors.tabBarBorder,
          borderTopWidth: 1,
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
        tabBarItemStyle: {
          paddingVertical: 2,
        },
      }}
    >
      <Tabs.Screen
        name="home"
        options={{
          title: 'Home',
          tabBarIcon: ({ color, size, focused }) => (
            <StandardTabIcon icon={Home} color={color} size={size} focused={focused} />
          ),
        }}
      />
      <Tabs.Screen
        name="strings"
        options={{
          title: 'Strings',
          tabBarIcon: ({ color, size, focused }) => (
            <StandardTabIcon icon={List} color={color} size={size} focused={focused} />
          ),
        }}
      />
      <Tabs.Screen
        name="recommend"
        options={{
          title: 'Recommend',
          tabBarIcon: ({ color, size, focused }) => (
            <StandardTabIcon icon={Zap} color={color} size={size} focused={focused} />
          ),
        }}
      />
      <Tabs.Screen
        name="bookings"
        options={{
          title: 'Bookings',
          tabBarIcon: ({ color, size, focused }) => (
            <StandardTabIcon icon={Calendar} color={color} size={size} focused={focused} />
          ),
        }}
      />
      <Tabs.Screen
        name="chat"
        options={{
          href: null,
          title: 'Chat',
        }}
      />
      <Tabs.Screen
        name="profile"
        options={{
          title: 'Profile',
          tabBarIcon: ({ color, size, focused }) => (
            <StandardTabIcon icon={User} color={color} size={size} focused={focused} />
          ),
        }}
      />
      <Tabs.Screen
        name="results"
        options={{
          href: null,
          title: 'Results',
        }}
      />
    </Tabs>
  );
}
