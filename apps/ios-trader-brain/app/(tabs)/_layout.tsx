import { Tabs } from "expo-router";

const tabs = [
  { name: "index", title: "HOME" },
  { name: "brain", title: "BRAIN" },
  { name: "portfolio", title: "PORTFOLIO" },
  { name: "orders", title: "ORDERS" },
  { name: "system", title: "SYSTEM" },
] as const;

export default function TabLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: true,
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
