import React, { useState } from 'react';
import { Tabs } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Calendar, Home, List, MoreHorizontal, User } from 'lucide-react-native';
import { Platform, View } from 'react-native';
import { PlayerToolsSheet } from '../../../components/player/PlayerToolsSheet';
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
    <View className="h-8 w-8 items-center justify-center">
      <Icon size={size} color={color} strokeWidth={focused ? 2.1 : 1.9} />
    </View>
  );
}

export default function TabsLayout() {
  const insets = useSafeAreaInsets();
  const [isMoreOpen, setIsMoreOpen] = useState(false);
  const bottomSpacing = Math.max(insets.bottom, 10);
  const tabBarHeight = 60 + bottomSpacing;

  return (
    <>
      <Tabs
        screenOptions={{
          headerShown: false,
          sceneStyle: {
            backgroundColor: appChromeColors.page,
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
            paddingTop: 4,
            paddingHorizontal: 2,
            marginHorizontal: 10,
            marginBottom: bottomSpacing,
            borderRadius: 14,
            ...(Platform.OS === 'web'
              ? { boxShadow: '0 10px 24px rgba(9, 29, 62, 0.16)' }
              : {
                  shadowColor: '#091D3E',
                  shadowOpacity: 0.16,
                  shadowOffset: { width: 0, height: 8 },
                  shadowRadius: 16,
                  elevation: 10,
                }),
            overflow: 'hidden',
          },
          tabBarLabelStyle: {
            fontSize: 10,
            fontWeight: '600',
            marginTop: 0,
          },
          tabBarItemStyle: {
            minHeight: 46,
            marginHorizontal: 0,
            marginVertical: 0,
            borderRadius: 10,
            overflow: 'hidden',
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
          title: 'More',
          tabBarAccessibilityLabel: 'Open more player features',
          tabBarIcon: ({ color, size, focused }) => (
            <StandardTabIcon icon={MoreHorizontal} color={color} size={size} focused={focused} />
          ),
        }}
        listeners={{
          tabPress: (event) => {
            event.preventDefault();
            setIsMoreOpen(true);
          },
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
      <PlayerToolsSheet visible={isMoreOpen} onClose={() => setIsMoreOpen(false)} />
    </>
  );
}
