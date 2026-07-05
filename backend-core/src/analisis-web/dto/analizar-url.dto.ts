import { IsNotEmpty, IsString } from 'class-validator';

export class AnalizarUrlDto {
  @IsString()
  @IsNotEmpty()
  url: string;
}
