import { AppText, CardContainer } from "../components/foundation";

const meta = {
  title: "Foundation/CardContainer",
  component: CardContainer,
};

export default meta;

export const Basic = {
  render: () => (
    <CardContainer>
      <AppText variant="title">Read-only shell</AppText>
      <AppText>No broker mutation.</AppText>
    </CardContainer>
  ),
};
