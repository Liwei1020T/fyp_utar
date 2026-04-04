import { Body, Controller, Get, Post, UseGuards } from '@nestjs/common';
import { ApiBearerAuth, ApiTags } from '@nestjs/swagger';
import { successResponse } from '../common/api-response';
import { CurrentUser } from '../common/decorators/current-user.decorator';
import { Public } from '../common/decorators/public.decorator';
import { JwtAuthGuard } from '../common/guards/jwt-auth.guard';
import { RolesGuard } from '../common/guards/roles.guard';
import { AuthenticatedUser } from '../common/types/authenticated-user.type';
import { AuthService } from './auth.service';
import { LoginDto } from './dto/login.dto';
import { RegisterDto } from './dto/register.dto';

@ApiTags('Auth')
@UseGuards(JwtAuthGuard, RolesGuard)
@Controller('auth')
export class AuthController {
  constructor(private readonly authService: AuthService) {}

  @Public()
  @Post('register')
  async register(@Body() dto: RegisterDto) {
    const data = await this.authService.registerCustomer(dto);
    return successResponse('Registration successful', data);
  }

  @Public()
  @Post('login')
  async login(@Body() dto: LoginDto) {
    const data = await this.authService.login(dto);
    return successResponse('Login successful', data);
  }

  @ApiBearerAuth('access-token')
  @Get('me')
  async me(@CurrentUser() user: AuthenticatedUser) {
    const data = await this.authService.getCurrentUser(user.sub);
    return successResponse('Current user fetched successfully', data);
  }
}
