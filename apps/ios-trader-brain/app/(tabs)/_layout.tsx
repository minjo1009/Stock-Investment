import { Tabs } from "expo-router";

const tabs = [
  { name: "index", title: "홈" },
  { name: "portfolio", title: "포트폴리오" },
  { name: "brain", title: "브레인" },
  { name: "orders", title: "주문" },
  { name: "system", title: "시스템" },
] as const;

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarLabelPosition: "below-icon",
      }}
    >
      {tabs.map((tab) => (
        <Tabs.Screen
          key={tab.name}
          name={tab.name}
          options={{ title: tab.title, tabBarLabel: tab.title }}
        />
      ))}
    </Tabs>
  );
}
