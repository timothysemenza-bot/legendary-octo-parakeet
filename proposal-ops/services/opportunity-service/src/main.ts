import { AppModule } from "./app.module";

// Bootstrap placeholder for NestFactory bootstrap once Nest dependencies are installed.
export function bootstrap(): AppModule {
  return new AppModule();
}

if (require.main === module) {
  const app = bootstrap();
  // eslint-disable-next-line no-console
  console.log("Opportunity service bootstrapped with controllers:", Object.keys(app));
}
