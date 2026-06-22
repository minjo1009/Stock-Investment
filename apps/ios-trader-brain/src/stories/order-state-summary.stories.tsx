import type { Meta, StoryObj } from "@storybook/react-native-web-vite";

import { OrderStateSummary } from "../components/domain";
import orderDetail from "../mocks/fixtures/order-detail.json";
import orders from "../mocks/fixtures/orders.json";
import type { OrderDetailReadModel, OrdersReadModel } from "../read-models";

const ordersFixture = orders as OrdersReadModel;
const orderDetailFixture = orderDetail as OrderDetailReadModel;

const meta = {
  title: "Domain/OrderStateSummary",
  component: OrderStateSummary,
} satisfies Meta<typeof OrderStateSummary>;

export default meta;

type Story = StoryObj<typeof meta>;

const args = {
  orderDetail: orderDetailFixture,
  orders: ordersFixture,
};

export const FreshSource: Story = { args };
export const StaleSource: Story = { args };
export const MissingSource: Story = { args };
export const UnknownSource: Story = { args };
export const Blocked: Story = { args };
export const DisabledAction: Story = { args };
export const ChartMissing: Story = { args };
export const SourceNotAttached: Story = { args };
