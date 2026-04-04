import React from 'react';
import { Tabs } from 'expo-router';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { Calendar, Home, List, MessageSquareText, User, Zap } from 'lucide-react-native';
import { View } from 'react-native';
import { HeroText, cn } from '../../../components/ui/heroui';
import { appChromeColors, appLayoutMetrics } from '../../../components/ui/theme';

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
        'h-10 w-10 items-center justify-center rounded-2xl',
        focused ? 'bg-primary-600/10' : 'bg-transparent'
      )}
    >
      <Icon size={size} color={color} strokeWidth={focused ? 2.1 : 1.9} />
    </View>
  );
}

export default function TabsLayout() {
  const insets = useSafeAreaInsets();
  const tabBarHeight = 74 + Math.max(insets.bottom, 10);

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
          borderWidth: 1,
          borderColor: appChromeColors.tabBarBorder,
          borderTopWidth: 1,
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
          tabBarIcon: () => (
            <View
              className="-mt-6 h-[66px] w-[66px] items-center justify-center rounded-full border-[6px] bg-primary-200/80 p-1.5 shadow-glow"
              style={{ borderColor: appChromeColors.page }}
            >
              <View className="h-full w-full items-center justify-center rounded-full bg-primary-600">
                <Zap size={26} color="white" strokeWidth={1.7} />
              </View>
            </View>
          ),
          tabBarLabel: ({ color, focused }) => (
            <HeroText
              style={{
                color,
                fontSize: 10,
                fontWeight: '800',
                marginTop: 8,
                letterSpacing: 0.6,
              }}
            >
              {focused ? 'AI RECO' : 'RECO'}
            </HeroText>
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
          title: 'Chat',
          tabBarIcon: ({ color, size, focused }) => (
            <StandardTabIcon icon={MessageSquareText} color={color} size={size} focused={focused} />
          ),
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
    </Tabs>
  );
}
